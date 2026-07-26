# Show Diaries client and responder versions in the client footer

## Objective

Display the build versions of both running parts of Diaries in every existing client footer:

```text
Client 0.1.1-build-123 · Responder 0.1.1-build-124
```

The responder version is obtained through a new unauthenticated MQTT-RPC handler in:

```text
com.rsmaxwell.diaries.responder.handlers
```

The client version is loaded from a build-generated static JSON asset. Keeping the values separate makes mismatched client and responder images immediately visible.

## Design

### Client version

The client reads `assets/build-info.json` through `ClientBuildInfoService`.

For day-to-day `ng serve`, the committed file contains a development snapshot value. During a Docker image build, the Dockerfile replaces that file with values supplied by the existing image build script.

### Responder version

The client calls the existing MQTT-RPC request topic with:

```json
{
  "function": "getVersion"
}
```

The responder registers a new `GetVersion` handler. It returns the responder's existing `BuildInfo` object with `Response.success(...)`.

The request deliberately does not require an access token. This allows the footer to show the responder version on sign-in and registration pages as well as authenticated pages.

### Footer display

A shared standalone `VersionInfoComponent` is added to all three existing footer components:

- `PlainfooterComponent`
- `FullfooterComponent`
- `PagefooterComponent`

The component displays fallback states without preventing the rest of the application from loading:

- `connecting` while waiting for the MQTT-RPC response;
- `unavailable` if the responder cannot be reached;
- `unknown` if the client build metadata cannot be loaded.

## Development steps

### 1. Correct the responder build name

Edit:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/buildinfo/BuildInfo.java
```

Change the build name from `diaries-response` to `diaries-responder`.

Add public getters for all build fields so Jackson can reliably serialise the object returned by MQTT-RPC.

### 2. Add the responder MQTT-RPC handler

Create:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/GetVersion.java
```

The handler should:

1. extend `RequestHandler`;
2. construct the responder `BuildInfo`;
3. log the version being returned;
4. return `Response.success(buildInfo)`;
5. perform no authentication checks.

No database or retained-topic-tree access is required.

### 3. Register the handler

Edit:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java
```

Import `GetVersion` and register it before the other handlers:

```java
messageHandler.putHandler("getVersion", new GetVersion());
```

The client and responder function names must match exactly.

### 4. Add the shared client build-info model

Create:

```text
diaries-client/src/app/model/build-info.ts
```

Use one interface for both the local client JSON and the responder MQTT-RPC reply. The field names match the responder build information:

- `name`
- `version`
- `buildID`
- `builddate`
- `gitCommit`
- `gitBranch`
- `gitURL`

### 5. Add the client build-info asset and service

Create:

```text
diaries-client/public/assets/build-info.json
```

This is the fallback used by day-to-day development.

Create:

```text
diaries-client/src/app/build-info/client-build-info.service.ts
```

The service loads `assets/build-info.json` with `HttpClient` and caches the result using `shareReplay` so each footer does not issue another HTTP request.

### 6. Add the unauthenticated client RPC method

Edit:

```text
diaries-client/src/app/mqtt/rpc.service.ts
```

Add `getResponderVersion$()`.

It should follow the existing unauthenticated `register$()` and `signin$()` pattern:

1. obtain the runtime configuration and MQTT connection;
2. use the normal client-specific reply topic;
3. send `{ function: 'getVersion' }`;
4. pass `null` as the access token;
5. deserialise the reply as `BuildInfo`.

Do not use `authorisedRpcRequest()` for this call, because the footer must work before sign-in.

### 7. Add the shared footer version component

Create:

```text
diaries-client/src/app/build-info/version-info.component.ts
diaries-client/src/app/build-info/version-info.component.html
diaries-client/src/app/build-info/version-info.component.scss
```

The component combines:

- the static client build-info request;
- the MQTT-RPC responder build-info request.

Only the `version` field from each response is shown in the footer.

### 8. Add the component to all existing footers

Edit all three footer TypeScript files to import `VersionInfoComponent`, and add it to each standalone component's `imports` array.

Edit all three footer templates and add:

```html
<app-version-info></app-version-info>
```

Edit each footer stylesheet to provide a small left margin before the version text.

### 9. Generate client build information during image creation

Edit:

```text
diaries-client/scripts/files/Dockerfile
```

Declare build arguments for the version and build metadata. Before running the Angular production build, overwrite:

```text
public/assets/build-info.json
```

with the supplied values.

This causes the metadata to become part of the built Angular assets and therefore part of the client image.

### 10. Pass all metadata into the Docker build

Edit:

```text
diaries-client/scripts/image.sh
```

In addition to the existing `VERSION`, `BUILD_DATE`, and `VCS_REF` arguments, pass:

- `BUILD_ID`
- `GIT_BRANCH`
- `GIT_URL`

The existing preparation/build pipeline remains the single source of the release version.

## Testing

### Responder test

Start the responder and use an MQTT-RPC request equivalent to:

```json
{
  "function": "getVersion"
}
```

Confirm that the successful response payload contains:

```json
{
  "name": "diaries-responder",
  "version": "...",
  "buildID": "...",
  "builddate": "...",
  "gitCommit": "...",
  "gitBranch": "...",
  "gitURL": "..."
}
```

Confirm the same call works without an access-token user property.

### Day-to-day client test

1. Start Mosquitto and the responder.
2. Run the Angular client with `ng serve`.
3. Open the sign-in page.
4. Confirm the footer initially shows `Responder connecting` and then changes to the responder version.
5. Confirm the client value is `0.0.0-SNAPSHOT` unless the development asset has been regenerated.
6. Navigate through pages using each footer variant and confirm the version appears consistently.

### Failure behaviour

1. Stop the responder or MQTT broker.
2. Reload the client.
3. Confirm the footer shows `Responder unavailable` after the RPC timeout.
4. Confirm the page remains usable and no redirect is triggered.

### Docker image test

1. Run the normal prepare and client image build process.
2. Start the built client image.
3. Open `assets/build-info.json` in the browser and confirm it contains the image version.
4. Confirm the same client version appears in the footer.
5. Start the matching responder image and confirm its version appears separately.

### Mismatch test

Run a client and responder built with different tags. Confirm that both different version strings are visible. This is the main operational benefit of showing the values separately.

## Complete changed files

Complete replacement versions of all changed and newly created files are included under:

```text
complete-source-files/
```

The directory preserves the source-tree paths so the files can be compared or copied directly into the Diaries working tree.

## Validation note

The source package was prepared from `diaries-sources-20260726-100555.zip`, which was treated as newer than GitHub. Automated compilation could not be completed in the isolated environment because the archive did not contain installed Angular dependencies and Gradle needed external network access to download its distribution. The changes should therefore be compiled and tested using the normal Diaries development environment before committing.
