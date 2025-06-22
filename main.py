from fastapi import FastAPI
from routes import auth, appointment, spent, payment

app = FastAPI()

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(appointment.router, prefix="/appointments", tags=["Appointments"])
app.include_router(spent.router, prefix="/spents", tags=["Spents"])
# app.include_router(payment.router, prefix="/payments", tags=["Payments"])

@app.get("/")
def read_root():
    return {"message": "Party App API running"}
