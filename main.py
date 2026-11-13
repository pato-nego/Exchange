from fastapi import FastAPI


@app.get("/health")
def health():
    return {"message": "Exchange is healthy"}