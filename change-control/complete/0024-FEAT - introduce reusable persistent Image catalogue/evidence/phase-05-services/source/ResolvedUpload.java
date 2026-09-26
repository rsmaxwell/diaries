package com.rsmaxwell.diaries.responder.utilities;

import java.nio.file.Path;

/** Immutable staging result. Only ImageCatalogueService creates these; complete or discard consumes the staged file. */
public final class ResolvedUpload {
    private final Path stagedFile;
    private final Path target;
    private final String relativePath;
    private final String originalFilename;
    private final ImageMetadataInspector.Inspection inspection;

    ResolvedUpload(Path stagedFile, Path target, String relativePath, String originalFilename,
            ImageMetadataInspector.Inspection inspection) {
        this.stagedFile = stagedFile;
        this.target = target;
        this.relativePath = relativePath;
        this.originalFilename = originalFilename;
        this.inspection = inspection;
    }
    public Path stagedFile() { return stagedFile; }
    public Path target() { return target; }
    public String relativePath() { return relativePath; }
    public String originalFilename() { return originalFilename; }
    public ImageMetadataInspector.Inspection inspection() { return inspection; }
}
