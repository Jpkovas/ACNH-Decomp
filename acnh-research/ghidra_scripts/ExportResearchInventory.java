// Export a versioned, local-only baseline. No inferred semantic names.
// @category ACNH.Research
import ghidra.app.script.GhidraScript;
import ghidra.app.util.headless.HeadlessScript;
import ghidra.program.model.address.*;
import ghidra.program.model.block.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.scalar.Scalar;
import com.google.gson.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

public class ExportResearchInventory extends HeadlessScript {
    private JsonObject addressRecord(Address address) {
        JsonObject r=new JsonObject();r.addProperty("address",address.toString());
        r.addProperty("relative_address",Long.toHexString(address.subtract(currentProgram.getImageBase())));
        return r;
    }
    private void write(File path,JsonElement content) throws Exception {
        try(Writer writer=new OutputStreamWriter(new FileOutputStream(path),StandardCharsets.UTF_8)) {
            new GsonBuilder().setPrettyPrinting().create().toJson(content,writer);
        }
    }
    public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length<2)throw new IllegalArgumentException("output-directory version-id [layout-only]");
        File out=new File(args[0]);out.mkdirs();String version=args[1];
        boolean layoutOnly=args.length>2&&args[2].equals("layout-only");
        JsonObject layout=new JsonObject();layout.addProperty("version_id",version);
        layout.addProperty("module","main");layout.addProperty("language",currentProgram.getLanguageID().toString());
        layout.addProperty("format",currentProgram.getExecutableFormat());
        layout.addProperty("image_base",currentProgram.getImageBase().toString());
        layout.addProperty("executable_sha256",currentProgram.getExecutableSHA256());
        layout.addProperty("ghidra_version",ghidra.framework.Application.getApplicationVersion());
        layout.addProperty("analysis_timeout",analysisTimeoutOccurred());
        JsonArray blocks=new JsonArray();
        for(MemoryBlock block:currentProgram.getMemory().getBlocks()) {
            JsonObject b=addressRecord(block.getStart());b.addProperty("name",block.getName());
            b.addProperty("size",block.getSize());b.addProperty("initialized",block.isInitialized());
            b.addProperty("read",block.isRead());b.addProperty("write",block.isWrite());b.addProperty("execute",block.isExecute());blocks.add(b);
        }
        layout.add("memory_blocks",blocks);write(new File(out,"import-layout.json"),layout);
        if(layoutOnly)return;
        int functionCount=0;long instructionCount=0;long blockCount=0;
        BasicBlockModel model=new BasicBlockModel(currentProgram);
        try(Writer fw=new BufferedWriter(new OutputStreamWriter(new FileOutputStream(new File(out,"functions.jsonl")),StandardCharsets.UTF_8))) {
            FunctionIterator functions=currentProgram.getFunctionManager().getFunctions(true);
            while(functions.hasNext()&&!monitor.isCancelled()) {
                Function function=functions.next();JsonObject row=addressRecord(function.getEntryPoint());
                row.addProperty("version_id",version);row.addProperty("module","main");row.addProperty("kind","function");
                row.addProperty("name",function.getName(true));row.addProperty("signature",function.getPrototypeString(false,false));
                row.addProperty("size",function.getBody().getNumAddresses());row.addProperty("thunk",function.isThunk());
                row.addProperty("name_status",function.getSymbol().getSource()==SourceType.DEFAULT?"provisional":"inferred");
                row.addProperty("confidence","low");row.addProperty("reviewed",false);
                JsonArray evidence=new JsonArray();evidence.add("ghidra_autoanalysis");row.add("evidence",evidence);
                JsonArray callers=new JsonArray();ReferenceIterator references=currentProgram.getReferenceManager().getReferencesTo(function.getEntryPoint());
                while(references.hasNext()) {Reference ref=references.next();Function caller=currentProgram.getFunctionManager().getFunctionContaining(ref.getFromAddress());if(caller!=null)callers.add(caller.getEntryPoint().toString());}
                row.add("callers",callers);
                JsonArray callees=new JsonArray();for(Function called:function.getCalledFunctions(monitor))callees.add(called.getEntryPoint().toString());row.add("callees",callees);
                JsonArray cfg=new JsonArray();CodeBlockIterator bit=model.getCodeBlocksContaining(function.getBody(),monitor);
                while(bit.hasNext()) {CodeBlock block=bit.next();JsonObject b=addressRecord(block.getFirstStartAddress());
                    JsonArray edges=new JsonArray();CodeBlockReferenceIterator dests=block.getDestinations(monitor);
                    while(dests.hasNext())edges.add(dests.next().getDestinationAddress().toString());b.add("edges",edges);cfg.add(b);blockCount++;}
                row.add("cfg",cfg);JsonArray mnemonics=new JsonArray();Set<String> constants=new TreeSet<>();Set<String> stringRefs=new TreeSet<>();
                InstructionIterator instructions=currentProgram.getListing().getInstructions(function.getBody(),true);
                while(instructions.hasNext()){
                    Instruction insn=instructions.next();mnemonics.add(insn.getMnemonicString());instructionCount++;
                    for(int operand=0;operand<insn.getNumOperands();operand++)for(Object object:insn.getOpObjects(operand))if(object instanceof Scalar)constants.add(Long.toUnsignedString(((Scalar)object).getUnsignedValue(),16));
                    for(Reference ref:insn.getReferencesFrom()) {Data target=currentProgram.getListing().getDataAt(ref.getToAddress());if(target!=null&&target.hasStringValue())stringRefs.add(String.valueOf(target.getValue()));}
                }
                JsonArray constantJson=new JsonArray();for(String value:constants)constantJson.add(value);row.add("scalar_constants",constantJson);
                JsonArray stringJson=new JsonArray();for(String value:stringRefs)stringJson.add(value);row.add("string_references",stringJson);
                row.add("mnemonics",mnemonics);fw.write(row.toString()+"\n");functionCount++;
                if(functionCount%5000==0)println("Exported "+functionCount+" functions");
            }
        }
        JsonArray externals=new JsonArray();
        FunctionIterator externalFunctions=currentProgram.getFunctionManager().getExternalFunctions();
        while(externalFunctions.hasNext()) {Function function=externalFunctions.next();JsonObject row=new JsonObject();
            row.addProperty("version_id",version);row.addProperty("module","main");row.addProperty("address",function.getEntryPoint().toString());
            row.addProperty("name",function.getName(true));row.addProperty("kind","external_function");row.addProperty("name_status","original");
            row.addProperty("confidence","medium");row.addProperty("signature_verified",false);externals.add(row);}
        write(new File(out,"externals.json"),externals);
        int stringCount=0;
        try(Writer sw=new BufferedWriter(new OutputStreamWriter(new FileOutputStream(new File(out,"strings.jsonl")),StandardCharsets.UTF_8))) {
            DataIterator data=currentProgram.getListing().getDefinedData(true);
            while(data.hasNext()&&!monitor.isCancelled()){Data datum=data.next();if(!datum.hasStringValue())continue;
                JsonObject row=addressRecord(datum.getAddress());row.addProperty("version_id",version);row.addProperty("value",String.valueOf(datum.getValue()));
                JsonArray refs=new JsonArray();ReferenceIterator it=currentProgram.getReferenceManager().getReferencesTo(datum.getAddress());
                while(it.hasNext())refs.add(it.next().getFromAddress().toString());row.add("xrefs",refs);sw.write(row.toString()+"\n");stringCount++;}
        }
        JsonObject summary=new JsonObject();summary.addProperty("version_id",version);summary.addProperty("functions_discovered",functionCount);
        summary.addProperty("instructions",instructionCount);summary.addProperty("basic_blocks",blockCount);summary.addProperty("strings",stringCount);
        summary.addProperty("reviewed_functions",0);summary.addProperty("high_confidence_semantic_names",0);
        summary.addProperty("external_functions",externals.size());
        summary.addProperty("analysis_timeout",analysisTimeoutOccurred());write(new File(out,"inventory-summary.json"),summary);
        println("ACNH inventory complete: "+summary);
    }
}
