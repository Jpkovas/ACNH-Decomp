// @category ACNH.Research
import ghidra.app.script.GhidraScript;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import com.google.gson.*;
public class VerifyRelativeRelocations extends GhidraScript {
    public void run() throws Exception {
        String[] args=getScriptArgs();if(args.length!=3)throw new IllegalArgumentException("expected-tsv output-json version-id");
        long base=currentProgram.getImageBase().getOffset();int checked=0;JsonArray failures=new JsonArray();
        try(var lines=Files.lines(Path.of(args[0]),StandardCharsets.UTF_8)) {
            for(String line:(Iterable<String>)lines::iterator) {
                if(monitor.isCancelled())throw new IllegalStateException("Relocation verification cancelled");
                String[] columns=line.split("\t");long offset=Long.parseUnsignedLong(columns[0],16);long target=Long.parseUnsignedLong(columns[1],16);
                long expected=base+target;long actual=currentProgram.getMemory().getLong(toAddr(base+offset));checked++;
                if(actual!=expected){JsonObject failure=new JsonObject();failure.addProperty("address",Long.toHexString(base+offset));failure.addProperty("expected",Long.toHexString(expected));failure.addProperty("actual",Long.toHexString(actual));failures.add(failure);}
            }
        }
        JsonObject report=new JsonObject();report.addProperty("version_id",args[2]);report.addProperty("relative_relocations_checked",checked);report.addProperty("mismatches",failures.size());report.add("failures",failures);
        Files.writeString(Path.of(args[1]),new GsonBuilder().setPrettyPrinting().create().toJson(report),StandardCharsets.UTF_8);
        println("Relocation verification: "+checked+" checked, "+failures.size()+" mismatches");
        if(!failures.isEmpty())throw new IllegalStateException("Relative relocation divergence");
    }
}
