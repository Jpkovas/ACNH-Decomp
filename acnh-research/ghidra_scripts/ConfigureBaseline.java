// @category ACNH.Research
import ghidra.app.script.GhidraScript;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.google.gson.*;
public class ConfigureBaseline extends GhidraScript {
    public void run() throws Exception {
        Map<String,String> before=getCurrentAnalysisOptionsAndValues(currentProgram);
        JsonObject changed=new JsonObject();
        for(String name:List.of("Decompiler Parameter ID","(Switch) IPC Analyzer")) {
            if(!before.containsKey(name))throw new IllegalStateException("Analysis option absent: "+name);
            JsonObject entry=new JsonObject();entry.addProperty("before",before.get(name));entry.addProperty("after","false");changed.add(name,entry);
            setAnalysisOption(currentProgram,name,"false");
        }
        JsonObject profile=new JsonObject();profile.addProperty("profile","ACNH baseline L1");profile.add("changed_options",changed);
        profile.addProperty("reason","Bulk prototype inference and SDK IPC scanning are separate experiments; decompile reviewed functions individually");
        profile.add("effective_options",new Gson().toJsonTree(getCurrentAnalysisOptionsAndValues(currentProgram)));
        String[] args=getScriptArgs();if(args.length==1)Files.writeString(Path.of(args[0]),new GsonBuilder().setPrettyPrinting().create().toJson(profile),StandardCharsets.UTF_8);
        println("Configured explicit ACNH baseline analysis profile");
    }
}
