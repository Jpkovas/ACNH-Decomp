// @category ACNH.Research
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.google.gson.*;
public class ExportAnchorFunctions extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();if(args.length<3)throw new IllegalArgumentException("output-directory version-id anchor-address...");
        Path out=Path.of(args[0]);Files.createDirectories(out);DecompInterface decompiler=new DecompInterface();decompiler.openProgram(currentProgram);
        Set<String> seen=new HashSet<>();Map<String,JsonObject> all=new TreeMap<>();
        if(Files.exists(out.resolve("summary.json")))for(JsonElement item:JsonParser.parseString(Files.readString(out.resolve("summary.json"))).getAsJsonArray()){
            JsonObject row=item.getAsJsonObject();if(!row.get("version_id").getAsString().equals(args[1]))throw new IllegalStateException("Existing anchor summary belongs to another version");all.put(row.get("address").getAsString(),row);
        }
        for(int i=2;i<args.length;++i){Function fn=getFunctionContaining(toAddr(args[i]));
            if(fn==null&&args[1].equals("1.0.0")&&args[i].equals("710000ac10")) {
                disassemble(toAddr(args[i]));Instruction first=getInstructionAt(toAddr(args[i]));Instruction second=getInstructionAt(toAddr(args[i]).add(4));
                if(first==null||second==null||!first.getMnemonicString().equalsIgnoreCase("mov")||!second.getMnemonicString().equalsIgnoreCase("ret"))throw new IllegalStateException("Pilot instruction shape differs");
                fn=createFunction(toAddr(args[i]),"returns_zero_candidate");
            }
            if(fn==null) {
                // Explicit caller-supplied anchors only. Names stay provisional; this is
                // not general function discovery or proof of a semantic signature.
                if(!currentProgram.getMemory().getBlock(toAddr(args[i])).isExecute())throw new IllegalStateException("Anchor is outside executable memory");
                disassemble(toAddr(args[i]));fn=createFunction(toAddr(args[i]),null);
            }
            if(fn==null)throw new IllegalStateException("Could not delimit function at anchor "+args[i]);
            String address=fn.getEntryPoint().toString();if(!seen.add(address))continue;
            DecompileResults results=decompiler.decompileFunction(fn,60,monitor);
            JsonObject record=new JsonObject();record.addProperty("version_id",args[1]);record.addProperty("module","main");record.addProperty("address",address);
            record.addProperty("size",fn.getBody().getNumAddresses());record.addProperty("tool_name",fn.getName());record.addProperty("tool_signature",fn.getPrototypeString(false,false));
            record.addProperty("decompile_completed",results.decompileCompleted());record.addProperty("decompile_error",results.getErrorMessage());
            JsonArray instructions=new JsonArray();InstructionIterator it=currentProgram.getListing().getInstructions(fn.getBody(),true);
            while(it.hasNext()){Instruction instruction=it.next();JsonObject insn=new JsonObject();insn.addProperty("address",instruction.getAddress().toString());insn.addProperty("assembly",instruction.toString());instructions.add(insn);}record.add("instructions",instructions);
            if(results.decompileCompleted())Files.writeString(out.resolve(address+".c"),results.getDecompiledFunction().getC(),StandardCharsets.UTF_8);
            Files.writeString(out.resolve(address+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(record),StandardCharsets.UTF_8);
            record.remove("instructions");all.put(address,record);println("Anchor function "+address+" size "+fn.getBody().getNumAddresses()+" decompiled="+results.decompileCompleted());
        }
        JsonArray summary=new JsonArray();for(JsonObject row:all.values())summary.add(row);
        decompiler.dispose();Files.writeString(out.resolve("summary.json"),new GsonBuilder().setPrettyPrinting().create().toJson(summary),StandardCharsets.UTF_8);
    }
}
