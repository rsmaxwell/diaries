# Stable `/files/...` URL regression

Step 4 removes the physical-directory/public-URL coupling in `UploadFile`.

The new focused test is:

```text
com.rsmaxwell.diaries.responder.handlers.UploadStagingTest.publicUrlAndPersistedPathDoNotExposePhysicalFilesDirectory
```

It configures the physical mutable directory as:

```text
files-development-common
```

and requires all of the following:

```text
physical file:              <temp-root>/files-development-common/image.txt
UploadFile response URL:    /files/image.txt
Image.relativePath:         image.txt
```

The test therefore prevents an environment-specific Files leaf from leaking into either the public URL or the durable Image catalogue path.

Run it on Windows with:

```bat
scripts\windows\validation\verify-0031-step4-runtime.bat
```

The runtime verifier first prepares and checks the effective direct-development responder config, then runs this focused Gradle test.
