// 0052-DEF: deterministic, high-quality RGB JPEG generation for an RGBA PNG.
// Requires Java 17+; run as: java WhitleyToJpeg.java source.png output.jpg
import java.awt.Color;
import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.File;
import java.util.Iterator;
import javax.imageio.ImageIO;
import javax.imageio.ImageWriteParam;
import javax.imageio.ImageWriter;
import javax.imageio.stream.ImageOutputStream;

public class WhitleyToJpeg {
  public static void main(String[] args) throws Exception {
    System.setProperty("java.awt.headless", "true");
    if (args.length != 2) throw new IllegalArgumentException("Usage: java WhitleyToJpeg.java source.png output.jpg");
    BufferedImage source = ImageIO.read(new File(args[0]));
    if (source == null || source.getWidth() != 776 || source.getHeight() != 502)
      throw new IllegalArgumentException("Approved map must decode as 776 x 502 pixels");
    BufferedImage rgb = new BufferedImage(source.getWidth(), source.getHeight(), BufferedImage.TYPE_INT_RGB);
    Graphics2D g = rgb.createGraphics();
    try {
      g.setColor(Color.WHITE);
      g.fillRect(0, 0, rgb.getWidth(), rgb.getHeight());
      g.drawImage(source, 0, 0, null);
    } finally { g.dispose(); }
    Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName("jpeg");
    if (!writers.hasNext()) throw new IllegalStateException("No JPEG encoder available in this JDK");
    ImageWriter writer = writers.next();
    try (ImageOutputStream stream = ImageIO.createImageOutputStream(new File(args[1]))) {
      writer.setOutput(stream);
      ImageWriteParam param = writer.getDefaultWriteParam();
      param.setCompressionMode(ImageWriteParam.MODE_EXPLICIT);
      param.setCompressionQuality(0.99f);
      writer.write(null, new javax.imageio.IIOImage(rgb, null, null), param);
    } finally { writer.dispose(); }
    BufferedImage check = ImageIO.read(new File(args[1]));
    if (check == null || check.getWidth() != 776 || check.getHeight() != 502)
      throw new IllegalStateException("Output JPEG failed decoding check");
    System.out.println("Created high-quality JPEG 776 x 502 (RGB, white composite)");
  }
}
