package com.rsmaxwell.diaries.responder.handlers;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.io.TempDir;
import org.eclipse.paho.mqttv5.common.packet.UserProperty;
import com.rsmaxwell.diaries.responder.config.*;
import com.rsmaxwell.diaries.responder.utilities.*;
import com.rsmaxwell.diaries.responder.dto.ListFilesResponse;
import com.rsmaxwell.mqtt.rpc.exceptions.RpcStatusException;

class UploadStagingTest {
    @TempDir Path root;
    DiaryContext context;
    List<UserProperty> editor;
    final Set<String> owned = new HashSet<>();
    java.util.function.Predicate<String> ownership = path -> owned.contains(path.toLowerCase(Locale.ROOT));
    UploadFile handler() {
        return new UploadFile() {
            @Override protected ImageCatalogueService.Catalogue uploadCatalogue(DiaryContext ignored) {
                return new ImageCatalogueService.Catalogue() {
                    public boolean owns(String path) { return ownership.test(path); }
                    public com.rsmaxwell.diaries.responder.model.Image insert(com.rsmaxwell.diaries.responder.model.Image image) {
                        fail("6.2 must not create catalogue rows"); return null;
                    }
                };
            }
        };
    }
    @BeforeEach void setup() throws Exception {
        context = new DiaryContext();
        context.setSecret(Base64.getEncoder().encodeToString("01234567890123456789012345678901".getBytes()));
        var config = new Config();
        var files = new DiariesConfig(); files.setRoot(root.toString()); files.setFiles("files");
        config.setDiaries(files); context.setConfig(config); Files.createDirectory(root.resolve("files"));
        editor = token("EDITOR");
    }
    List<UserProperty> token(String role) {
        return List.of(new UserProperty("accessToken", Authorization.getTokenWithClaims(context.getSecret(), "access", 5,
            java.time.temporal.ChronoUnit.MINUTES, Map.of("status", "ACTIVE", "role", role))));
    }
    byte[] png() throws Exception {
        try (var in = getClass().getResourceAsStream("/image-inspection/sample.png")) { return in.readAllBytes(); }
    }
    Map<String,Object> args(byte[] bytes) {
        var args = new HashMap<String,Object>();
        args.put("name", "image.txt"); args.put("contentType", "application/octet-stream");
        args.put("size", (long)bytes.length); args.put("bytes", Base64.getEncoder().encodeToString(bytes)); return args;
    }
    void cleanStaging() throws Exception {
        Path stage = root.resolve("files/.image-staging");
        if (Files.exists(stage)) try (var entries = Files.list(stage)) { assertTrue(entries.allMatch(p -> p.getFileName().toString().equals("catalogue.lock"))); }
    }
    @Test void validImageKeepsLegacyResponseAndGenericFilesStillWork() throws Exception {
        var args = args(png()); args.put("subdir", "Maps\\.\\new"); args.put("sha256", "");
        var response = handler().handleRequest(context, args, editor);
        var payload = (Map<?,?>)response.payload();
        assertEquals(Set.of("name","subdir","size","path","url"), payload.keySet());
        assertEquals("Maps/new", payload.get("subdir"));
        assertEquals("/files/Maps/new/image.txt", payload.get("url"));
        assertArrayEquals(png(), Files.readAllBytes(root.resolve("files/Maps/new/image.txt")));
        var generic=args("generic bytes".getBytes()); generic.put("name","data.bin");
        handler().handleRequest(context,generic,editor);
        assertEquals("generic bytes", Files.readString(root.resolve("files/data.bin")));
        cleanStaging();
    }
    @Test void allRejectedInputsLeaveExistingBytesAndNoParts() throws Exception {
        Files.writeString(root.resolve("files/image.txt"),"original");
        var cases = new ArrayList<Map<String,Object>>();
        for (var override : List.<Map<String,Object>>of(
            Map.of("bytes","!!!"), Map.of("bytes","YQ==trailing", "size",1L), Map.of("size",-1L),
            Map.of("size",1L), Map.of("sha256","a".repeat(64)), Map.of("contentType","image/jpeg"),
            Map.of("subdir","a/../b"), Map.of("subdir",".image-staging"), Map.of("name","C:\\bad"))) {
            var args=args(png()); args.put("overwrite",true); args.putAll(override); cases.add(args);
        }
        var truncated = args(Arrays.copyOf(png(), 20)); truncated.put("overwrite",true); cases.add(truncated);
        for (var args:cases) {
            assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args,editor));
            assertEquals("original",Files.readString(root.resolve("files/image.txt"))); cleanStaging();
        }
    }
    @Test void conflictAndPromotionFailureCleanStaging() throws Exception {
        Files.writeString(root.resolve("files/image.txt"),"original");
        assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args(png()),editor));
        cleanStaging();
        Files.createDirectory(root.resolve("files/directory"));
        var args=args(png()); args.put("name","directory"); args.put("overwrite",true);
        assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args,editor)); cleanStaging();
    }
    @Test void authenticationPrecedesAnyFileWork() throws Exception {
        assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args(png()),List.of()));
        assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args(png()),token("VIEWER")));
        assertFalse(Files.exists(root.resolve("files/.image-staging")));
    }
    @Test void reservedDirectoryCannotBeListedOrDeletedAndDoesNotAppearInListing() throws Exception {
        Path stage=Files.createDirectory(root.resolve("files/.image-staging"));
        Files.writeString(stage.resolve("private.png"),"private");
        Files.createDirectory(root.resolve("files/public"));
        var listing=(ListFilesResponse)new ListFiles().handleRequest(context,Map.of(),editor).payload();
        assertEquals(List.of("public"),listing.getItems().stream().map(ImageItem::name).toList());
        for(String directory:List.of(".image-staging",".IMAGE-STAGING","x/../.image-staging")) {
            assertThrows(RpcStatusException.class, () -> new ListFiles().handleRequest(context,Map.of("subdir",directory),editor));
            assertThrows(RpcStatusException.class, () -> new DeleteFile().handleRequest(context,Map.of("subdir",directory,"name","private.png"),editor));
        }
        assertEquals("private",Files.readString(stage.resolve("private.png")));
    }
    @Test void ownedPathsAndAliasesAreConflictsEvenWhenFileMissing() throws Exception {
        owned.add("maps/image.txt");
        Files.createDirectory(root.resolve("files/maps"));
        Path original=root.resolve("files/maps/image.txt"); Files.writeString(original,"original");
        for(boolean missing:List.of(false,true)) {
            if(missing) Files.delete(original);
            for(boolean overwrite:List.of(false,true)) for(String directory:List.of("maps","MAPS","maps\\.")) {
                var args=args(png()); args.put("subdir",directory); args.put("overwrite",overwrite);
                var failure=assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args,editor));
                assertEquals(409,failure.getStatus().code());
                if(!missing) assertEquals("original",Files.readString(original));
                else assertFalse(Files.exists(original));
            }
        }
        assertEquals(Set.of("maps/image.txt"),owned); cleanStaging();
    }
    @Test void ownershipIsRecheckedUnderLockBeforeChangingTarget() throws Exception {
        var calls=new java.util.concurrent.atomic.AtomicInteger();
        ownership=path -> calls.incrementAndGet() >= 2;
        Path original=root.resolve("files/image.txt"); Files.writeString(original,"original");
        var args=args(png()); args.put("overwrite",true);
        var failure=assertThrows(RpcStatusException.class, () -> handler().handleRequest(context,args,editor));
        assertEquals(409,failure.getStatus().code()); assertEquals(2,calls.get());
        assertEquals("original",Files.readString(original)); cleanStaging();
    }
    @Test void uncataloguedOverwriteSucceedsWithoutCreatingRows() throws Exception {
        Files.writeString(root.resolve("files/image.txt"),"original");
        var args=args(png()); args.put("overwrite",true);
        handler().handleRequest(context,args,editor);
        assertArrayEquals(png(),Files.readAllBytes(root.resolve("files/image.txt")));
        assertTrue(owned.isEmpty()); cleanStaging();
    }
    @Test void simultaneousNoOverwriteRequestsHaveOneWinner() throws Exception {
        var args=args(png());
        try(var pool=java.util.concurrent.Executors.newFixedThreadPool(2)) {
            java.util.concurrent.Callable<Boolean> request=() -> {
                try { handler().handleRequest(context,args,editor); return true; }
                catch(RpcStatusException failure) { assertEquals(409,failure.getStatus().code()); return false; }
            };
            var results=pool.invokeAll(List.of(request,request));
            assertNotEquals(results.get(0).get(),results.get(1).get());
        }
        assertArrayEquals(png(),Files.readAllBytes(root.resolve("files/image.txt"))); cleanStaging();
    }
    @Test void missingCatalogueConfigurationFailsClosed() throws Exception {
        assertThrows(RpcStatusException.class, () -> new UploadFile().handleRequest(context,args(png()),editor));
        assertFalse(Files.exists(root.resolve("files/image.txt")));
    }

}
