// =========================================================
// AI Product Assistant - Frontend
// =========================================================


const chatbot = document.querySelector(".chatbot-container");

const toggleButton = document.getElementById("chatbot-toggle");

const closeButton = document.getElementById("chatbot-close");

const sendButton = document.getElementById("chatbot-send");

const input = document.getElementById("chatbot-input");

const messages = document.getElementById("chatbot-messages");

const typing = document.getElementById("chatbot-typing");


// =========================================================
// Open Chatbot
// =========================================================

toggleButton.addEventListener("click", function () {

    chatbot.style.display = "flex";

    input.focus();

});


// =========================================================
// Close Chatbot
// =========================================================

closeButton.addEventListener("click", function () {

    chatbot.style.display = "none";

});


// =========================================================
// Add Message
// =========================================================

function addMessage(message, type) {

    const messageDiv = document.createElement("div");

    messageDiv.classList.add(
        "chat-message",
        type === "user"
            ? "user-message"
            : "bot-message"
    );


    const bubble = document.createElement("div");

    bubble.classList.add("message-bubble");

    bubble.textContent = message;


    messageDiv.appendChild(bubble);

    messages.appendChild(messageDiv);


    // Scroll to latest message

    messages.scrollTop = messages.scrollHeight;
}


// =========================================================
// Add Product Cards
// =========================================================

function addProductCards(products) {

    // No products
    if (!products || products.length === 0) {
        return;
    }


    const container = document.createElement("div");

    container.classList.add("product-cards-container");


    products.forEach(function (product) {

        const card = document.createElement("div");

        card.classList.add("chat-product-card");


        card.innerHTML = `
            <div class="chat-product-info">

                <h4>
                    ${escapeHtml(product.name)}
                </h4>

                <p class="chat-product-category">
                    ${escapeHtml(product.category || "Product")}
                </p>

                <p class="chat-product-price">
                    ₹${Number(product.price).toLocaleString("en-IN")}
                </p>

                <p class="chat-product-stock">
                    ${
                        Number(product.stock) > 0
                            ? "In Stock"
                            : "Out of Stock"
                    }
                </p>

                <button
                    class="view-product-btn"
                    onclick="viewProduct(${product.id})"
                >
                    View Product
                </button>

            </div>
        `;


        container.appendChild(card);

    });


    messages.appendChild(container);


    // Scroll to latest product cards

    messages.scrollTop = messages.scrollHeight;
}


// =========================================================
// Escape HTML
// =========================================================

function escapeHtml(text) {

    const div = document.createElement("div");

    div.textContent = text;

    return div.innerHTML;
}


// =========================================================
// View Product
// =========================================================

function viewProduct(productId) {

    window.location.href = `/product/${productId}`;

}


// =========================================================
// Send Message
// =========================================================

async function sendMessage() {

    const question = input.value.trim();


    if (!question) {
        return;
    }


    // Show user's message

    addMessage(
        question,
        "user"
    );


    // Clear input

    input.value = "";


    // Show typing indicator

    typing.classList.remove("hidden");


    sendButton.disabled = true;


    try {

        // ---------------------------------------------
        // Send request to Flask
        // ---------------------------------------------

        const response = await fetch("/api/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: question
            })

        });


        // ---------------------------------------------
        // DEBUG: HTTP status
        // ---------------------------------------------

        console.log(
            "Chatbot HTTP Status:",
            response.status
        );


        // ---------------------------------------------
        // Get JSON response
        // ---------------------------------------------

        const data = await response.json();


        // ---------------------------------------------
        // DEBUG: API response
        // ---------------------------------------------

        console.log(
            "Chatbot API Response:",
            data
        );


        // ---------------------------------------------
        // Check response
        // ---------------------------------------------

        if (data.success) {

            // AI chatbot response

            addMessage(
                data.answer,
                "bot"
            );


            // Product cards

            addProductCards(
                data.products
            );


        } else {

            console.error(
                "Chatbot API Error:",
                data.error
            );


            addMessage(
                data.error || "Sorry, something went wrong.",
                "bot"
            );

        }


    } catch (error) {

        // ---------------------------------------------
        // DEBUG: JavaScript / Network error
        // ---------------------------------------------

        console.error(
            "Chatbot Error:",
            error
        );


        addMessage(
            "Unable to connect to the AI assistant.",
            "bot"
        );

    } finally {

        typing.classList.add("hidden");

        sendButton.disabled = false;

        input.focus();

    }

}


// =========================================================
// Send Button
// =========================================================

sendButton.addEventListener(
    "click",
    sendMessage
);


// =========================================================
// Enter Key
// =========================================================

input.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            sendMessage();

        }

    }
);