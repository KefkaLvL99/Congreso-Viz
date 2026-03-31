#!/bin/bash
cd /Users/alvaro/Documents/Proyectos/congreso-viz/backend/fase2_api
source SENADO/bin/activate
source .env
export $(cat .env | xargs)
uvicorn main:app --reload