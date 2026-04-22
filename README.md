# DuckReminder

Desktop pet en Python con `tkinter` y `Pillow` que muestra un pato pixel art caminando por la pantalla con un cartel recordatorio.

## Funciones

- Ventana de configuracion para cambiar el texto del cartel
- Ajuste del intervalo entre apariciones
- Vista previa inmediata del pato
- Opcion para iniciar con Windows
- Minimizar a la bandeja del sistema
- Generacion de `.exe` y de instalador para Windows

## Requisitos

- Python 3.12
- Pillow
- pystray
- PyInstaller para compilar el ejecutable
- Inno Setup para compilar el instalador

## Ejecutar

```bash
python main.py
```

## Generar EXE

```bash
build_exe.bat
```

## Generar instalador

```bash
build_installer.bat
```

## Archivos importantes

- `main.py`: aplicacion principal
- `locales/`: textos de la interfaz en espanol e ingles
- `build_exe.bat`: compila el `.exe`
- `build_installer.bat`: compila el `.exe` y el instalador
- `installer.iss`: script de Inno Setup
- `CREDITS.md`: atribucion y notas de licencia del sprite

## Nota sobre el sprite

El sprite del pato fue tomado de una publicacion de la comunidad de Aseprite y no debe asumirse como libre para uso comercial. Revisa `CREDITS.md` antes de redistribuir o monetizar este proyecto.
