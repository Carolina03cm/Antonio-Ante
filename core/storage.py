STORAGES = {
    "default": {
        "BACKEND": "core.storage.VercelBlobStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}