// Explicit reviewed annotations only. No guessed bulk renaming or signature propagation.
// @category ACNH.Research
import ghidra.app.script.GhidraScript;
import ghidra.program.model.listing.*;
import ghidra.program.model.data.*;
import ghidra.program.model.symbol.SourceType;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import com.google.gson.*;
public class ImportValidatedSymbols extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();if(args.length!=2)throw new IllegalArgumentException("annotations-json report-json");
        JsonObject input=JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
        if(!currentProgram.getExecutableSHA256().equalsIgnoreCase(input.get("executable_sha256").getAsString()))throw new IllegalStateException("Annotation provenance differs from executable");
        int count=0;
        for(JsonElement item:input.getAsJsonArray("symbols")) {
            JsonObject symbol=item.getAsJsonObject();var address=toAddr(symbol.get("address").getAsString().replace("0x",""));
            MemoryBlockCheck(address);
            Function fn=getFunctionAt(address);if(fn==null){disassemble(address);fn=createFunction(address,null);}
            if(fn==null||!fn.getEntryPoint().equals(address))throw new IllegalStateException("Annotation has no function entry");
            fn.setName(symbol.get("name").getAsString(),SourceType.USER_DEFINED);
            setPlateComment(address,"Research annotation, version "+input.get("version_id").getAsString()+". "+symbol.toString());count++;
        }
        JsonObject layout=input.getAsJsonObject("partial_parameter_layout");
        StructureDataType type=new StructureDataType(new CategoryPath("/ACNHResearch/"+input.get("version_id").getAsString()),layout.get("name").getAsString(),layout.get("size").getAsInt());
        for(JsonElement field:layout.getAsJsonArray("fields")) {
            JsonObject f=field.getAsJsonObject();type.replaceAtOffset(f.get("offset").getAsInt(),UnsignedIntegerDataType.dataType,f.get("size").getAsInt(),f.get("name").getAsString(),"Observed field in a partial slice");
        }
        currentProgram.getDataTypeManager().addDataType(type,DataTypeConflictHandler.REPLACE_HANDLER);
        JsonObject report=new JsonObject();report.addProperty("version_id",input.get("version_id").getAsString());report.addProperty("functions_annotated",count);
        report.addProperty("annotations_sha256",HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(args[0])))));
        report.addProperty("partial_parameter_slices_added",1);report.addProperty("function_signatures_overridden",0);report.addProperty("whole_object_layouts_asserted",0);
        Files.writeString(Path.of(args[1]),new GsonBuilder().setPrettyPrinting().create().toJson(report));println(report.toString());
    }
    private void MemoryBlockCheck(ghidra.program.model.address.Address address) throws Exception {
        var block=currentProgram.getMemory().getBlock(address);if(block==null||!block.isExecute())throw new IllegalStateException("Annotation outside executable block");
    }
}
