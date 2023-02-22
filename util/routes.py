from resources.user import SignupApi, LoginApi, TokenApi, LogoutApi, LogoutRefreshAPI
from resources.home import BoardsApi, BoardApi
from resources.boardItems import ByBoardApi
from resources.board import ItemsApi, ItemApi, UploadURLs


def initialize_routes(api):
    api.add_resource(SignupApi, '/api/auth/signup')
    api.add_resource(LoginApi, '/api/auth/login')
    api.add_resource(TokenApi, '/api/auth/refresh')
    api.add_resource(LogoutApi, '/api/auth/logout')
    api.add_resource(LogoutRefreshAPI, '/api/auth/revoke')

    api.add_resource(ItemsApi, '/api/items')
    api.add_resource(ItemApi, '/api/item/<id>')

    api.add_resource(BoardsApi, '/api/boards')
    api.add_resource(BoardApi, '/api/board/<id>')

    # Get items by board slug
    api.add_resource(ByBoardApi, '/api/by-board/<id>')

    api.add_resource(UploadURLs, '/api/UploadURLs')
