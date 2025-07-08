from semantic_router import Route
from semantic_router.routers import SemanticRouter
from semantic_router.encoders import HuggingFaceEncoder



encoder = HuggingFaceEncoder(
    name="sentence-transformers/all-MiniLM-L6-v2"
)

faq = Route(
    name='faq',
    utterances=[
        "What is Flipkart return policy?",
        "How do I initiate a return on Flipkart?",
        "How long does it take to get a refund from Flipkart?",
        "Are there any items that cannot be returned?",
        "What are the conditions for a successful return?",
        "Can I exchange a product instead of returning it?",
        "What is Flipkart refund policy for prepaid orders?",
        "How will I get my refund if I paid via Cash on Delivery?"
    ]
)

sql = Route(
    name='sql',
    utterances=[
        "i want to buy nike shoes that have 50% discount.",
        "Are there any shoes under 3000?",
        "Do you have formal shoes of size 9",
        "Are there any puma shoes in sale?",
        "what is the price of puma running shoes",
        "show me all Nike shoes with rating more than 4.5",
        "top 10 shoes with best rating",
        "list formal shoes below 2000 rupees",
        "filter by rating above 4.8",
        "what are the most discounted shoes",
        "get all reebok shoes under 4000",
        "list of shoes sorted by price",
        "find adidas shoes with high discount and good rating",
        "cheapest shoes in stock",
        "show shoes in the 3000 to 5000 price range",
    ]
)

router = SemanticRouter(routes=[faq, sql], encoder=encoder, auto_sync="local")


if __name__ == "__main__":
    print(router("How do I initiate a return on Flipkart?").name)
    print(router("Are there any shoes under 3000?").name)