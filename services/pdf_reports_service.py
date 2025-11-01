from fastapi.responses import FileResponse
from weasyprint import HTML
from datetime import datetime
import os
import markdown2
import google.generativeai as genai
from repositories.kitchen_config import get_by
from repositories.kitchen_type import get_type_by_id
from services.assigment_service import send_message_to_ai


# Configurar tu clave de API


def format_ai_response(text: str) -> str:
    """Convierte el texto Markdown del modelo en HTML con formato limpio."""
    return markdown2.markdown(
        text,
        extras=["fenced-code-blocks", "tables", "strike", "underline", "break-on-newline"]
    )


def generate_pdf(config_id, user_id, db):
    # Obtener configuración de cocina
    kitchen_config = get_by(user_id, config_id, db)
    if not kitchen_config:
        raise Exception("Kitchen configuration not found")

    kitchen_type = get_type_by_id(db, kitchen_config.kitchen_type_id)
    if not kitchen_type:
        raise Exception("Kitchen type not found")

    # Obtener recomendaciones del modelo de IA
    recommendation_text = send_message_to_ai(user_id, config_id, db)
    recommendation_html = format_ai_response(recommendation_text)

    # Generar imagen basada en la descripción

    # Fecha actual
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Contenido HTML del PDF
    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Open Sans', sans-serif;
                margin: 40px;
                color: #2c3e50;
                line-height: 1.6;
            }}
            h1, h2, h3 {{
                color: #1a5276;
                margin-top: 25px;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .image-section {{
                text-align: center;
                margin: 25px 0;
            }}
            .image-section img {{
                max-width: 100%;
                height: auto;
                border: 1px solid #ccc;
                border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            }}
            footer {{
                margin-top: 50px;
                font-size: 12px;
                text-align: center;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h1>Informe de Organización de Cocina</h1>
        <p><strong>Fecha:</strong> {current_date}</p>
        <hr>
        <h2>Datos de Configuración</h2>
        <table>
            <tr><th>Campo</th><th>Valor</th></tr>
            <tr><td>Tipo de cocina</td><td>{kitchen_type.type}</td></tr>
            <tr><td>Área disponible</td><td>{kitchen_config.area} m²</td></tr>
            <tr><td>Número de estaciones</td><td>{kitchen_config.num_stations}</td></tr>
            <tr><td>Número de empleados</td><td>{kitchen_config.staff_count}</td></tr>
            <tr><td>Notas</td><td>{kitchen_config.notes}</td></tr>
        </table>

        <h2>Distribución y Recomendaciones</h2>
        <div>{recommendation_html}</div>

        <footer>
            Generado automáticamente por <strong>AI Kitchen Planner</strong> — {current_date}
        </footer>
    </body>
    </html>
    """

    # Crear carpeta si no existe
    output_dir = "generated_pdfs"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"kitchen_report_{config_id}.pdf")

    # Generar el PDF
    HTML(string=html_content).write_pdf(output_path)

    # Devolver el PDF como respuesta
    return FileResponse(
        path=output_path,
        filename=f"reporte_cocina_{config_id}.pdf",
        media_type="application/pdf"
    )
