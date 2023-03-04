from fastapi import FastAPI, APIRouter
import uvicorn

class BaseAgent():

    def __init__(self):
        self.app = FastAPI()
    
    def run(self, host="localhost", port=3000):
        uvicorn.run(self.app, host=host, port=port)