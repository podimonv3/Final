from aiohttp import web

routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("MATRIX ONLINE")

async def init_web_application():
    """Initializes the standard web layout factory interface for Koyeb health checks."""
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app
