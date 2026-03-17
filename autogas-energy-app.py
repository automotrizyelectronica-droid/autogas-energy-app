def subir_foto(file_bytes, nombre, mime_type):
    try:
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
        metadata = {
            'name': nombre,
            'parents': [ID_CARPETA_FOTOS]
        }

        archivo = drive_service.files().create(
            body=metadata,
            media_body=media,
            fields='id',
            supportsAllDrives=True
        ).execute()

        file_id = archivo.get('id')

        # 👉 Hacer pública la imagen
        drive_service.permissions().create(
            fileId=file_id,
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()

        return file_id

    except Exception as e:
        return f"Err_{str(e)}"
