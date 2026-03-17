
# from fastapi import FastAPI, Request
# import uvicorn
# from ai.agents.NaturalLanguageDatabase import ask_db
# from ai.agents.NaturalLanguageEmailDesigner import ask_email_designer, edit_email_section

# # Initialize FastAPI app
# app = FastAPI(docs_url="/", openapi_url="/openapi.json")


# # AI Route
# @app.post("/ai-agent")
# async def ai_agent():
#     try:
#         response = ""#AI req
#         return {"response": response.choices[0].message["content"].strip()}
#     except Exception as e:
#         return {"error": str(e)}



# if __name__ == '__main__':
#     uvicorn.run("ai.__main__:app", host="127.0.0.1", port=443, reload=True)