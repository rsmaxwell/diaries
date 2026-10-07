# Step 13 client `ng serve` template-type correction

During live Step 13 setup, `npm start` reached Angular application compilation but failed strict template checking at the Files catalogue Space-key binding:

```text
NG5: Argument of type 'Event' is not assignable to parameter of type 'KeyboardEvent'.
(keydown.space)="onFileSpace(f, $event)"
```

The component handler accepted `KeyboardEvent`, while Angular types the `$event` from this key-specific template binding as `Event`. The handler uses only `preventDefault()` before delegating to `onFileClick`, whose existing parameter is already `Event`.

The production correction is therefore deliberately narrow:

```ts
onFileSpace(file: FileEntry, ev: Event): void
```

There is no behavioural change: a browser `KeyboardEvent` is an `Event`, Space still prevents the anchor default and selects only a valid selectable catalogue Image, and the existing keyboard-accessibility tests remain semantically applicable.

After applying this correction, rerun `npm start`. Step 13 remains open until both live gate phases are completed.
