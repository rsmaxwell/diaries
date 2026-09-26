-- PostgreSQL 18 catalogue contract, generated from the reviewed schema.sql.
-- Comparing structure, not row counts, sequence position or object OIDs.
\ir catalog-shape.sql
SELECT :'image_catalog_shape'::jsonb = $contract$
{
  "rules": 0,
  "table": {
    "kind": "r",
    "options": null,
    "partition": false,
    "tablespace": "0",
    "persistence": "p",
    "rowSecurity": false,
    "forceRowSecurity": false
  },
  "columns": [
    {
      "name": "id",
      "type": "bigint",
      "default": null,
      "notNull": true,
      "identity": "d",
      "position": 1,
      "collation": "-",
      "generated": ""
    },
    {
      "name": "version",
      "type": "bigint",
      "default": "0",
      "notNull": true,
      "identity": "",
      "position": 2,
      "collation": "-",
      "generated": ""
    },
    {
      "name": "relative_path",
      "type": "text",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 3,
      "collation": "\"default\"",
      "generated": ""
    },
    {
      "name": "mime_type",
      "type": "character varying(127)",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 4,
      "collation": "\"default\"",
      "generated": ""
    },
    {
      "name": "original_filename",
      "type": "text",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 5,
      "collation": "\"default\"",
      "generated": ""
    },
    {
      "name": "width",
      "type": "integer",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 6,
      "collation": "-",
      "generated": ""
    },
    {
      "name": "height",
      "type": "integer",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 7,
      "collation": "-",
      "generated": ""
    },
    {
      "name": "checksum",
      "type": "character(64)",
      "default": null,
      "notNull": true,
      "identity": "",
      "position": 8,
      "collation": "\"default\"",
      "generated": ""
    },
    {
      "name": "caption",
      "type": "text",
      "default": "''::text",
      "notNull": true,
      "identity": "",
      "position": 9,
      "collation": "\"default\"",
      "generated": ""
    },
    {
      "name": "alt_text",
      "type": "text",
      "default": "''::text",
      "notNull": true,
      "identity": "",
      "position": 10,
      "collation": "\"default\"",
      "generated": ""
    }
  ],
  "indexes": [
    {
      "live": true,
      "name": "image_checksum_idx",
      "ready": true,
      "valid": true,
      "unique": false,
      "options": null,
      "primary": false,
      "definition": "CREATE INDEX image_checksum_idx ON public.image USING btree (checksum)",
      "tablespace": "0",
      "nullsNotDistinct": false
    },
    {
      "live": true,
      "name": "image_pkey",
      "ready": true,
      "valid": true,
      "unique": true,
      "options": null,
      "primary": true,
      "definition": "CREATE UNIQUE INDEX image_pkey ON public.image USING btree (id)",
      "tablespace": "0",
      "nullsNotDistinct": false
    },
    {
      "live": true,
      "name": "image_relative_path_ci_uq",
      "ready": true,
      "valid": true,
      "unique": true,
      "options": null,
      "primary": false,
      "definition": "CREATE UNIQUE INDEX image_relative_path_ci_uq ON public.image USING btree (lower((relative_path COLLATE pg_unicode_fast)))",
      "tablespace": "0",
      "nullsNotDistinct": false
    }
  ],
  "policies": 0,
  "sequence": {
    "max": 9223372036854775807,
    "min": 1,
    "name": "image_id_seq",
    "type": "bigint",
    "cache": 1,
    "cycle": false,
    "start": 1,
    "increment": 1,
    "persistence": "p",
    "ownerMatchesTable": true,
    "identityDependency": true,
    "schema": "public"
  },
  "constraints": [
    {
      "name": "image_checksum_check",
      "type": "c",
      "deferred": false,
      "noInherit": false,
      "validated": true,
      "deferrable": false,
      "definition": "CHECK ((checksum ~ '^[0-9a-f]{64}$'::text))",
      "enforced": true
    },
    {
      "name": "image_height_check",
      "type": "c",
      "deferred": false,
      "noInherit": false,
      "validated": true,
      "deferrable": false,
      "definition": "CHECK ((height > 0))",
      "enforced": true
    },
    {
      "name": "image_mime_type_check",
      "type": "c",
      "deferred": false,
      "noInherit": false,
      "validated": true,
      "deferrable": false,
      "definition": "CHECK (((mime_type)::text = ANY ((ARRAY['image/jpeg'::character varying, 'image/png'::character varying, 'image/gif'::character varying, 'image/webp'::character varying])::text[])))",
      "enforced": true
    },
    {
      "name": "image_pkey",
      "type": "p",
      "deferred": false,
      "noInherit": true,
      "validated": true,
      "deferrable": false,
      "definition": "PRIMARY KEY (id)",
      "enforced": true
    },
    {
      "name": "image_version_check",
      "type": "c",
      "deferred": false,
      "noInherit": false,
      "validated": true,
      "deferrable": false,
      "definition": "CHECK ((version >= 0))",
      "enforced": true
    },
    {
      "name": "image_width_check",
      "type": "c",
      "deferred": false,
      "noInherit": false,
      "validated": true,
      "deferrable": false,
      "definition": "CHECK ((width > 0))",
      "enforced": true
    }
  ],
  "inheritance": 0,
  "userTriggers": 0,
  "droppedColumns": 0,
  "invalidNotNullConstraints": 0
}
$contract$::jsonb AS image_schema_exact
\gset
\if :image_schema_exact
\echo 0024 exact Image schema verified
\else
SELECT jsonb_pretty(:'image_catalog_shape'::jsonb) AS unexpected_image_schema;
DO $$ BEGIN RAISE EXCEPTION 'Partial or incompatible Image schema; no automatic repair is permitted'; END $$;
\endif
