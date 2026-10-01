import java.awt.Color;
import java.awt.Font;
import java.awt.image.BufferedImage;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.imageio.ImageIO;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import com.rsmaxwell.diaries.web.TestData;
import com.rsmaxwell.diaries.web.buildinfo.BuildInfo;
import com.rsmaxwell.diaries.web.config.AppConfig;
import com.rsmaxwell.diaries.web.http.WebServer;

/** Evidence-only launcher: unchanged reader and TestData, synthetic scan bytes. */
public final class BaselineSite {
    public static void main(String[] args) throws Exception {
        Path work = Path.of(args[0]).toAbsolutePath().normalize();
        Path evidence = Path.of(args[1]).toAbsolutePath().normalize();
        Path stop = work.resolve("stop");
        if (Files.exists(stop)) throw new IllegalStateException("Remove the previous owned stop marker before rerunning");
        Files.createDirectories(work);
        Path images = Files.createTempDirectory(work, "images-");
        Path scan = images.resolve("synthetic-page.jpg");
        BufferedImage pixels = new BufferedImage(1200, 800, BufferedImage.TYPE_INT_RGB);
        var drawing = pixels.createGraphics();
        drawing.setColor(new Color(247, 241, 221));
        drawing.fillRect(0, 0, 1200, 800);
        drawing.setColor(new Color(64, 56, 42));
        drawing.setFont(new Font(Font.SERIF, Font.PLAIN, 26));
        drawing.drawString("Synthetic diary page - 0026 baseline", 30, 55);
        drawing.setFont(new Font(Font.SERIF, Font.PLAIN, 18));
        drawing.drawString("A diary entry", 30, 95);
        drawing.drawString("Fixture content only. No personal diary or NAS files.", 30, 135);
        drawing.setColor(new Color(205, 199, 181));
        for (int y = 175; y < 780; y += 42) drawing.drawLine(25, y, 1175, y);
        drawing.dispose();
        ImageIO.write(pixels, "jpg", scan.toFile());

        AppConfig original = TestData.config("");
        AppConfig config = new AppConfig(
                new AppConfig.HttpConfig("127.0.0.1", 18082, "", "http://127.0.0.1:18082"),
                new AppConfig.MqttConfig("127.0.0.1", 18883, "diaries-web-0026-baseline",
                        "diaries0026baseline", 30, 2, 1, true),
                original.projection(),
                new AppConfig.ContentConfig("http://127.0.0.1:18083", "http://127.0.0.1:18083", "diaries"),
                original.site());
        new ObjectMapper().writerWithDefaultPrettyPrinter()
                .writeValue(evidence.resolve("runtime-config.synthetic.json").toFile(), config);
        Files.writeString(evidence.resolve("fixture-runtime.txt"),
                "pid=" + ProcessHandle.current().pid() + "\nimages=" + images + "\nstop=" + stop
                + "\nMQTT client is not started; projection uses unchanged TestData.readyProjection().\n");

        HttpServer content = HttpServer.create(new InetSocketAddress("127.0.0.1", 18083), 0);
        content.createContext("/diaries/", exchange -> {
            try (exchange) {
                String path = exchange.getRequestURI().getPath();
                if (!path.matches("/diaries/Family diary/page 00[123]\\.jpg")
                        || !(exchange.getRequestMethod().equals("GET") || exchange.getRequestMethod().equals("HEAD"))) {
                    exchange.sendResponseHeaders(404, -1);
                    return;
                }
                exchange.getResponseHeaders().set("Content-Type", "image/jpeg");
                byte[] body = Files.readAllBytes(scan);
                exchange.sendResponseHeaders(200, exchange.getRequestMethod().equals("HEAD") ? -1 : body.length);
                if (exchange.getRequestMethod().equals("GET")) exchange.getResponseBody().write(body);
            }
        });
        try (var projection = TestData.readyProjection();
                var web = new WebServer(config, projection,
                        new BuildInfo("diaries-web", "0026-baseline", "synthetic", "synthetic",
                                "e8d3470d6e65cf126319625a16fb308d7729454b", "main", "synthetic"))) {
            content.start();
            web.start();
            System.out.println("0026 baseline ready: http://127.0.0.1:18082; stop using " + stop);
            while (!Files.exists(stop)) Thread.sleep(250);
        } finally {
            content.stop(0);
            Files.deleteIfExists(scan);
            Files.deleteIfExists(images);
            System.out.println("0026 owned HTTP services closed; temporary image directory removed.");
        }
    }
}
