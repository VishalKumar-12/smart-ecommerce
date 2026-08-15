# =========================================================
# AI Product Assistant - Chatbot API
# =========================================================

from flask import Blueprint, request, jsonify

from ai.chatbot import generate_chatbot_response


# =========================================================
# Create Blueprint
# =========================================================

chatbot_bp = Blueprint(
    "chatbot",
    __name__,
    url_prefix="/api"
)


# =========================================================
# POST /api/chat
# =========================================================

@chatbot_bp.route("/chat", methods=["POST"])
def chat():

    try:

        # -------------------------------------------------
        # Get JSON data
        # -------------------------------------------------

        data = request.get_json()

        if not data:
            return jsonify({
                "success": False,
                "error": "Request body is required."
            }), 400


        # -------------------------------------------------
        # Get question
        # -------------------------------------------------

        question = data.get("message", "").strip()

        if not question:
            return jsonify({
                "success": False,
                "error": "Message cannot be empty."
            }), 400


        # -------------------------------------------------
        # RAG + Llama
        # -------------------------------------------------

        result = generate_chatbot_response(question)


        # -------------------------------------------------
        # Return response + products
        # -------------------------------------------------

       return jsonify({
         "success": True,
         "message": question,
         "answer": result["answer"],
         "products": result["products"]
       }), 200


    except Exception as e:

        # -------------------------------------------------
        # DEBUG ERROR
        # -------------------------------------------------

        print("========================================")
        print("CHATBOT ERROR:", repr(e))
        print("========================================")

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
