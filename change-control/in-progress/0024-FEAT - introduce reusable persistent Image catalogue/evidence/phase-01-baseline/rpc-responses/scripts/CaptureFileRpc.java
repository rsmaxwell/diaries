import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.concurrent.*;
import javax.imageio.ImageIO;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.rsmaxwell.diaries.responder.config.Config;
import com.rsmaxwell.diaries.responder.config.DiariesConfig;
import com.rsmaxwell.diaries.responder.handlers.*;
import com.rsmaxwell.diaries.responder.utilities.Authorization;
import com.rsmaxwell.diaries.responder.utilities.DiaryContext;
import com.rsmaxwell.mqtt.rpc.responder.MessageHandler;
import org.eclipse.paho.mqttv5.client.*;
import org.eclipse.paho.mqttv5.client.persist.MemoryPersistence;
import org.eclipse.paho.mqttv5.common.*;
import org.eclipse.paho.mqttv5.common.packet.*;

/** Actual production handlers/dispatcher over MQTT 5, isolated from DB and diary content. */
public class CaptureFileRpc {
    static final ObjectMapper JSON = new ObjectMapper();
    static final String REQUEST = "diaries/rpc/request";
    static final String REPLY = "diaries/rpc/0024-baseline/response";
    static final long MTIME = 1704164645000L;
    final Path output, files;
    final MqttAsyncClient publisher, listener, requestor;
    final BlockingQueue<Map.Entry<String, MqttMessage>> replies = new LinkedBlockingQueue<>();
    final List<Map<String, Object>> cases = new ArrayList<>();
    final String editor, reader;

    CaptureFileRpc(Path output, Path work, String broker) throws Exception {
        this.output = output;
        if (Files.exists(output) || Files.exists(work)) throw new IllegalArgumentException("Output and work must be new directories");
        Files.createDirectories(output.resolve("raw"));
        Files.createDirectories(output.resolve("normalized"));
        files = Files.createDirectories(work.resolve("files"));
        byte[] key = new byte[32]; new SecureRandom().nextBytes(key);
        String secret = Base64.getEncoder().encodeToString(key);
        editor = token(secret, "EDITOR"); reader = token(secret, "READER");
        Config config = new Config();
        DiariesConfig diaries = new DiariesConfig();
        diaries.setRoot(work.toString()); diaries.setFiles("files"); diaries.setDiaries("diaries");
        config.setDiaries(diaries);
        DiaryContext context = new DiaryContext(); context.setConfig(config); context.setSecret(secret);
        MessageHandler dispatcher = new MessageHandler();
        dispatcher.setContext(context);
        dispatcher.putHandler("uploadFile", new UploadFile());
        dispatcher.putHandler("listFiles", new ListFiles());
        dispatcher.putHandler("deleteFile", new DeleteFile());
        String suffix = UUID.randomUUID().toString();
        publisher = client(broker, "capture-pub-" + suffix);
        listener = client(broker, "capture-listen-" + suffix);
        requestor = client(broker, "capture-request-" + suffix);
        dispatcher.setPublisherClient(publisher); dispatcher.setListenerClient(listener);
        context.setPublisherClient(publisher);
        listener.setCallback(new Callback() {
            public void messageArrived(String topic, MqttMessage message) throws Exception {
                dispatcher.messageArrived(topic, message);
            }
        });
        requestor.setCallback(new Callback() {
            public void messageArrived(String topic, MqttMessage message) { replies.add(Map.entry(topic, message)); }
        });
        for (var c : List.of(publisher, listener, requestor)) c.connect(new MqttConnectionOptions()).waitForCompletion(10000);
        listener.subscribe(REQUEST, 1).waitForCompletion(10000);
        requestor.subscribe(REPLY, 1).waitForCompletion(10000);
    }
    static MqttAsyncClient client(String broker, String id) throws Exception {
        return new MqttAsyncClient(broker, id, new MemoryPersistence());
    }
    static String token(String secret, String role) {
        return Authorization.getTokenWithClaims(secret, "access", 30, ChronoUnit.MINUTES,
            Map.of("userId", 1L, "sessionId", "0024-synthetic-session", "status", "ACTIVE", "role", role));
    }
    void capture(String id, String function, Map<String, Object> args, String auth) throws Exception {
        byte[] correlation = UUID.randomUUID().toString().getBytes(StandardCharsets.UTF_8);
        Map<String, Object> request = Map.of("function", function, "args", args);
        MqttMessage message = new MqttMessage(JSON.writeValueAsBytes(request));
        MqttProperties props = new MqttProperties();
        props.setResponseTopic(REPLY); props.setCorrelationData(correlation);
        if (!auth.equals("missing")) props.getUserProperties().add(new UserProperty("accessToken",
            auth.equals("editor") ? editor : auth.equals("reader") ? reader : "invalid-synthetic-token"));
        message.setProperties(props); message.setQos(0); message.setRetained(false);
        requestor.publish(REQUEST, message).waitForCompletion(10000);
        var received = replies.poll(15, TimeUnit.SECONDS);
        if (received == null) throw new IllegalStateException("No reply: " + id);
        MqttMessage response = received.getValue();
        if (!received.getKey().equals(REPLY) || !Arrays.equals(correlation, response.getProperties().getCorrelationData()))
            throw new IllegalStateException("Reply correlation/topic mismatch: " + id);
        var userProperties = response.getProperties().getUserProperties().stream()
            .map(p -> Map.of("key", p.getKey(), "value", p.getValue())).toList();
        String statusText = response.getProperties().getUserProperties().stream()
            .filter(p -> p.getKey().equals("status")).findFirst().orElseThrow().getValue();
        var status = JSON.readTree(statusText);
        String payloadText = new String(response.getPayload(), StandardCharsets.UTF_8);
        Map<String, Object> raw = new LinkedHashMap<>();
        raw.put("caseId", id); raw.put("capturedAtUtc", Instant.now().toString());
        raw.put("requestTopic", REQUEST); raw.put("request", request);
        raw.put("requestAuth", auth); // Tokens are never archived.
        raw.put("requestQos", 0); raw.put("requestRetain", false);
        raw.put("responseTopic", received.getKey()); raw.put("correlationDataBase64", Base64.getEncoder().encodeToString(correlation));
        raw.put("responseQos", response.getQos()); raw.put("responseRetain", response.isRetained());
        raw.put("responseDuplicate", response.isDuplicate());
        raw.put("responseProperties", JSON.valueToTree(response.getProperties()));
        raw.put("responseUserProperties", userProperties);
        raw.put("payloadBase64", Base64.getEncoder().encodeToString(response.getPayload())); raw.put("payloadUtf8", payloadText);
        write(output.resolve("raw/" + id + ".json"), raw);
        Map<String, Object> normalized = new LinkedHashMap<>();
        normalized.put("caseId", id); normalized.put("function", function); normalized.put("auth", auth);
        normalized.put("status", JSON.readTree(normalize(statusText)));
        normalized.put("responseQos", response.getQos()); normalized.put("responseRetain", response.isRetained());
        try { normalized.put("payload", JSON.readTree(normalize(payloadText))); normalized.put("payloadFormat", "json"); }
        catch (Exception e) { normalized.put("payload", normalize(payloadText)); normalized.put("payloadFormat", "text"); }
        write(output.resolve("normalized/" + id + ".json"), normalized);
        cases.add(normalized);
        System.out.println(id + ": " + status.path("code").asInt() + " " + status.path("message").asText());
    }
    String normalize(String json) {
        String encodedRoot = JSON.valueToTree(files.toString()).toString();
        return json.replace(encodedRoot.substring(1, encodedRoot.length() - 1), "<FILES_ROOT>");
    }
    void editor(String id, String function, Map<String, Object> args) throws Exception { capture(id, function, args, "editor"); }
    static Map<String, Object> upload(String name, String subdir, String type, byte[] bytes) throws Exception {
        Map<String, Object> args = new LinkedHashMap<>();
        args.put("name", name); if (subdir != null) args.put("subdir", subdir);
        args.put("contentType", type); args.put("size", bytes.length);
        args.put("bytes", Base64.getEncoder().encodeToString(bytes));
        args.put("sha256", HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes)));
        return args;
    }
    static byte[] png() throws Exception {
        var out = new ByteArrayOutputStream(); ImageIO.write(new BufferedImage(2, 3, BufferedImage.TYPE_INT_RGB), "png", out); return out.toByteArray();
    }
    static byte[] jpegWithDate() throws Exception {
        var out = new ByteArrayOutputStream(); ImageIO.write(new BufferedImage(4, 5, BufferedImage.TYPE_INT_RGB), "jpeg", out);
        byte[] jpeg = out.toByteArray();
        // EXIF IFD0 DateTime tag. Fixed UTC JVM timezone makes epoch conversion repeatable.
        byte[] date = "2020:01:02 03:04:05\0".getBytes(StandardCharsets.US_ASCII);
        ByteBuffer tiff = ByteBuffer.allocate(26 + date.length).order(ByteOrder.LITTLE_ENDIAN);
        tiff.put((byte)'I').put((byte)'I').putShort((short)42).putInt(8).putShort((short)1);
        tiff.putShort((short)0x132).putShort((short)2).putInt(date.length).putInt(26).putInt(0).put(date);
        byte[] exif = new byte[6 + tiff.array().length];
        System.arraycopy(new byte[]{'E','x','i','f',0,0}, 0, exif, 0, 6);
        System.arraycopy(tiff.array(), 0, exif, 6, tiff.array().length);
        var result = new ByteArrayOutputStream(); result.write(jpeg, 0, 2);
        result.write(new byte[]{(byte)0xff, (byte)0xe1, (byte)((exif.length+2)>>8), (byte)(exif.length+2)});
        result.write(exif); result.write(jpeg, 2, jpeg.length-2); return result.toByteArray();
    }
    void run() throws Exception {
        byte[] png = png(), generic = "0024 synthetic generic file\n".getBytes(StandardCharsets.UTF_8), jpeg = jpegWithDate();
        Files.createDirectories(output.resolve("fixtures"));
        Files.write(output.resolve("fixtures/plain.png"), png); Files.write(output.resolve("fixtures/dated.jpg"), jpeg);
        Files.write(output.resolve("fixtures/generic.bin"), generic);
        editor("list-empty-root", "listFiles", Map.of());
        Files.createDirectories(files.resolve("empty")); Files.createDirectories(files.resolve("zeta"));
        Files.createDirectories(files.resolve("alpha/nested space"));
        editor("list-empty-nested", "listFiles", Map.of("subdir", "alpha/nested space"));
        var rootImage = upload("plain.png", null, "image/png", png);
        editor("upload-image-root", "uploadFile", rootImage);
        editor("upload-generic-root", "uploadFile", upload("generic.bin", null, "application/octet-stream", generic));
        editor("upload-image-octet-nested", "uploadFile", upload("image space.png", "alpha/nested space", "application/octet-stream", png));
        editor("upload-image-date", "uploadFile", upload("dated.jpg", null, "image/jpeg", jpeg));
        editor("upload-duplicate", "uploadFile", rootImage);
        var overwrite = upload("generic.bin", null, "application/octet-stream", generic); overwrite.put("overwrite", true);
        editor("upload-overwrite-generic", "uploadFile", overwrite);
        editor("upload-invalid-subdir", "uploadFile", upload("invalid.png", "../escape", "image/png", png));
        editor("upload-invalid-name", "uploadFile", upload("../invalid.png", null, "image/png", png));
        var wrongSize = upload("size.png", null, "image/png", png); wrongSize.put("size", png.length+1);
        editor("upload-size-mismatch", "uploadFile", wrongSize);
        var wrongHash = upload("hash.png", null, "image/png", png); wrongHash.put("sha256", "0".repeat(64));
        editor("upload-hash-mismatch", "uploadFile", wrongHash);
        editor("upload-unsupported-type", "uploadFile", upload("plain.txt", null, "text/plain", generic));
        try (var entries = Files.walk(files)) { for (Path p : entries.toList()) Files.setLastModifiedTime(p, FileTime.fromMillis(MTIME)); }
        Files.setLastModifiedTime(files.resolve("dated.jpg"), FileTime.fromMillis(MTIME+1000));
        editor("list-populated-root", "listFiles", Map.of());
        editor("list-populated-nested", "listFiles", Map.of("subdir", "alpha/nested space"));
        editor("list-missing-directory", "listFiles", Map.of("subdir", "does-not-exist"));
        editor("list-invalid-subdir", "listFiles", Map.of("subdir", "../escape"));
        editor("delete-image-existing", "deleteFile", Map.of("name", "plain.png"));
        editor("delete-image-missing", "deleteFile", Map.of("name", "plain.png"));
        editor("delete-generic-existing", "deleteFile", Map.of("name", "generic.bin"));
        editor("delete-generic-missing", "deleteFile", Map.of("name", "generic.bin"));
        editor("delete-image-nested", "deleteFile", Map.of("name", "image space.png", "subdir", "alpha/nested space"));
        editor("delete-invalid-name", "deleteFile", Map.of("name", "../invalid.png"));
        editor("delete-invalid-subdir", "deleteFile", Map.of("name", "invalid.png", "subdir", "../escape"));
        for (String auth : List.of("missing", "invalid", "reader")) {
            capture("upload-auth-"+auth, "uploadFile", upload("auth.png", null, "image/png", png), auth);
            capture("list-auth-"+auth, "listFiles", Map.of(), auth);
            capture("delete-auth-"+auth, "deleteFile", Map.of("name", "dated.jpg"), auth);
        }
        if (!Files.exists(files.resolve("dated.jpg")) || Files.exists(files.resolve("auth.png"))) throw new IllegalStateException("Unauthorized mutation");
        write(output.resolve("cases.json"), cases);
        Map<String, Object> environment = new LinkedHashMap<>();
        environment.put("captureTimeUtc", Instant.now().toString()); environment.put("javaVersion", System.getProperty("java.version"));
        environment.put("os", System.getProperty("os.name")); environment.put("timezone", TimeZone.getDefault().getID());
        environment.put("filesRoot", files.toString()); environment.put("caseCount", cases.size());
        environment.put("execution", "Production MessageHandler and file handlers through MQTT 5; synthetic signed EDITOR/READER claims; no database or full responder startup");
        write(output.resolve("environment.json"), environment);
    }
    static void write(Path path, Object value) throws Exception {
        Files.writeString(path, JSON.writerWithDefaultPrettyPrinter().writeValueAsString(value)+"\n", StandardOpenOption.CREATE_NEW);
    }
    void close() { for (var c : List.of(requestor, listener, publisher)) try { if(c.isConnected()) c.disconnect().waitForCompletion(5000); c.close(); } catch(Exception ignored) {} }
    public static void main(String[] args) throws Exception {
        if(args.length!=2) throw new IllegalArgumentException("Usage: CaptureFileRpc.java <new-output-dir> <new-work-dir>");
        TimeZone.setDefault(TimeZone.getTimeZone("UTC"));
        var capture = new CaptureFileRpc(Path.of(args[0]).toAbsolutePath().normalize(), Path.of(args[1]).toAbsolutePath().normalize(), "tcp://127.0.0.1:18884");
        try { capture.run(); } finally { capture.close(); }
    }
    static class Callback implements MqttCallback {
        public void disconnected(MqttDisconnectResponse r) {}
        public void mqttErrorOccurred(MqttException e) { e.printStackTrace(); }
        public void messageArrived(String topic, MqttMessage m) throws Exception {}
        public void deliveryComplete(IMqttToken t) {}
        public void connectComplete(boolean reconnect, String serverURI) {}
        public void authPacketArrived(int reasonCode, MqttProperties properties) {}
    }
}
