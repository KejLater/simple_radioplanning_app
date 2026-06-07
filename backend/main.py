from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional

from backend.models import RadiolineInput, RadiolineResult
from backend.radioline import Radioline

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / 'templates'
STATIC_DIR = BASE_DIR / 'static'


app = FastAPI(title="Radioline RSSI Calculator")


templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница с формой"""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "result": None,
            "error": None,
            "form_data": None
        }
    )


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(
    request: Request,
    Ptx: float = Form(...),
    Gtx: float = Form(...),
    Grx: float = Form(...),
    d: float = Form(...),
    f: float = Form(...),
    rain_density: Optional[str] = Form(None)
):
    """Обработка формы и расчет RSSI"""
    try:
        input_data = RadiolineInput(
            Ptx=Ptx,
            Gtx=Gtx,
            Grx=Grx,
            d=d,
            f=f,
            rain_density=rain_density
        )
        

        rl = Radioline(
            Ptx=input_data.Ptx,
            Gtx=input_data.Gtx,
            Grx=input_data.Grx,
            d=input_data.d,
            f=input_data.f,
            rain_density=input_data.rain_density
        )
        
        result = RadiolineResult(
            RSSI=round(rl.RSSI, 2),
            FSPL=round(rl.FSPL, 2),
            rain_attenuation=round(rl.rain_attenuation, 2),
            atmosphere_attenuation=round(rl.atmosphere_attenuation, 2)
        )
        
        form_data = {
            "Ptx": Ptx,
            "Gtx": Gtx,
            "Grx": Grx,
            "d": d,
            "f": f,
            "rain_density": rain_density
        }
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": result.dict(),
                "form_data": form_data,
                "error": None
            }
        )
        
    except ValueError as e:
        form_data = {
            "Ptx": Ptx,
            "Gtx": Gtx,
            "Grx": Grx,
            "d": d,
            "f": f,
            "rain_density": rain_density
        }
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "form_data": form_data,
                "error": str(e)
            }
        )
    except Exception as e:
        form_data = {
            "Ptx": Ptx,
            "Gtx": Gtx,
            "Grx": Grx,
            "d": d,
            "f": f,
            "rain_density": rain_density
        }
        
        return templates.TemplateResponse(
            "index.html",
            {
                "request": request,
                "result": None,
                "form_data": form_data,
                "error": f"Calculation error: {str(e)}"
            }
        )