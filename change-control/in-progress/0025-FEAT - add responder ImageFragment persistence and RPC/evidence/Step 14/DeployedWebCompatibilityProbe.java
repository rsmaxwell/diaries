import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import com.rsmaxwell.diaries.web.mqtt.*;
import com.rsmaxwell.diaries.web.projection.ProjectionEvent;
public class DeployedWebCompatibilityProbe {
 public static void main(String[] args) throws Exception {
  String json = Files.readString(Path.of(args[0]));
  var decoder = new RetainedMessageDecoder(new TopicParser("diaries"));
  var explicit = decoder.decode("diaries/fragments/33", json.getBytes(StandardCharsets.UTF_8));
  var absent = decoder.decode("diaries/fragments/33", json.replace("\"imageId\":null,", "").getBytes(StandardCharsets.UTF_8));
  if (!(explicit instanceof ProjectionEvent.UpsertFragment) || !explicit.equals(absent))
   throw new AssertionError("Additive null changed MARQUEE decode");
  System.out.println("PASS: deployed web build 5 decodes MARQUEE with imageId:null identically to absent imageId");
 }
}
