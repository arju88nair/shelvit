from flask import Response, request
from werkzeug.utils import secure_filename

from database.model import Item, User, Board
from flask_restful import Resource
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, ValidationError, InvalidQueryError
from util.errors import SchemaValidationError, InternalServerError, DeletingItemError, ItemNotExistsError, \
    ItemAlreadyExistsError, UpdatingItemError
from util.helpers import validateURL
import json
from util.slugGenerator import generateSlug
from flask_jwt_extended import jwt_required, get_jwt_identity
# from util.summariser import summarize, get_keywords
from bson.json_util import dumps
from bson import ObjectId
import requests
from bookmarks_converter import BookmarksConverter


class ItemsApi(Resource):
    """[Batch Item actions]
    """

    @jwt_required()
    def get(self):
        """[Retrieves all Items]

        Raises:
            InternalServerError: [If Error in retrieval]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            items = Item.objects().to_json()
            print(type(items))
            data = {'data': json.loads(items), 'message': "Successfully retrieved", "count": len(json.loads(items))}
            data = json.dumps(data)
            response = Response(data, mimetype="application/json", status=200)
            return response
        except Exception as e:
            raise InternalServerError

    @jwt_required()
    def post(self):
        """[Batch Item API]

        Raises:
            SchemaValidationError: [If there are validation error in the item data]
            ItemAlreadyExistsError: [If the item already exist]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # source validations
        if 'board' not in body:
            raise SchemaValidationError

        source = body['source']
        source_url = body['source_url']
        board = body['board']
        tags = body['tags']

        if source is None or source == '':
            raise SchemaValidationError
        if source_url is None or source_url == '':
            raise SchemaValidationError
        if board is None or board == '':
            raise SchemaValidationError
        if validateURL(source_url) is False:
            raise SchemaValidationError

        body['source'] = source
        body['source_url'] = source_url
        body['slug'] = generateSlug()
        body['tags'] = tags
        body['bookmark_created'] = body['bookmark_created']
        print(body)

        try:
            user_id = get_jwt_identity()
            user = User.objects.get(id=user_id)
            newBoard = Board.objects.get(slug=board)
            body['board'] = newBoard
            item = Item(**body, added_by=user, )
            item.save()
            item_id = item.id
            data = json.dumps({'id': str(item_id), 'message': "Successfully inserted"})
            return Response(data, mimetype="application/json", status=200)
        except (FieldDoesNotExist, ValidationError) as e:
            print(e)
            raise SchemaValidationError
        except NotUniqueError:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class ItemApi(Resource):
    """[Individual Item actions]
    """

    @jwt_required()
    def put(self, id):
        """[Updating single]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            SchemaValidationError: [If there are validation error in the item data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        body = request.get_json()

        # source validations
        if 'source' not in body or 'source_url' not in body or 'board' not in body:
            raise SchemaValidationError

        source = body['source']
        source_url = body['source_url']
        board = body['board']

        if source is None or source == '':
            raise SchemaValidationError

        if source_url is None or source_url == '':
            raise SchemaValidationError

        if board is None or board == '':
            raise SchemaValidationError

        try:
            user_id = get_jwt_identity()
            body = request.get_json()
            Item.objects.get(id=id, added_by=user_id).update(**body)
            data = json.dumps({'message': "Successfully updated"})
            return Response(data, mimetype="application/json", status=200)
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingItemError
        except Exception:
            raise InternalServerError

    @jwt_required()
    def delete(self, id):
        """[Deleting single item]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            DeletingItemError: [Error in deletion]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            item = Item.objects.get(id=id, added_by=user_id)
            item.delete()
            data = json.dumps({'message': "Successfully deleted"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise DeletingItemError
        except Exception:
            raise InternalServerError

    @jwt_required()
    def get(self, id):
        """[Get single item item]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            ItemNotExistsError: [Can't find the item item]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        try:
            user_id = get_jwt_identity()
            items = Item.objects.aggregate(
                {"$match": {"_id": ObjectId(id)}},
                {"$lookup": {
                    "from": "board",
                    "foreignField": "_id",
                    "localField": "board",
                    "as": "board",
                }},
                {"$unwind": "$board"},
            )
            item = list(items)
            data = dumps({'data': item[0], 'message': "Successfully retrieved"})
            return Response(data, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ItemNotExistsError
        except Exception as e:
            print(e)
            raise InternalServerError


class UploadURLs(Resource):
    """[Individual Item actions]
        """

    @jwt_required()
    def post(self):
        """[Updating single]

        Arguments:
            id {[Object ID]} -- [Mongo Object ID]

        Raises:
            SchemaValidationError: [If there are validation error in the item data]
            UpdatingItemError: [Error in update]
            InternalServerError: [Error in insertion]

        Returns:
            [json] -- [Json object with message and status code]
        """
        from bs4 import BeautifulSoup, NavigableString, Tag
        try:

            if request.method == 'POST':
                # upload = request.files['file']
                # # print(upload)
                # # path = upload.temporary_file_path
                f = request.files['file']

                fic = open(f.filename, "r")

                from time import strftime, localtime
                import sys
                sys.setrecursionlimit(10000)

                from bs4 import BeautifulSoup
                soup = BeautifulSoup(fic, 'lxml')
                item = soup.find_all('dl')[3]

                dt = soup.find_all('dt')
                boards = []
                body = {}
                folder_name = ''
                for i in dt:
                    n = i.find_next()
                    if n.name == 'h3':
                        folder_name = n.text
                        boards.append(folder_name)
                        continue
                    else:
                        user_id = get_jwt_identity()
                        user = User.objects.get(id=user_id)
                        # new_time = strftime('%Y-%m-%d %H:%M:%S', localtime(n.get("add_date")))
                        # print(new_time)
                        body['source'] = n.text
                        if n.get("tags") or n.get("href") is not None:
                            body['tags'] = n.get("tags")
                        if n.get("href") or n.get("href") is not None:
                            body['source_url'] = n.get("href")
                        # if n.get("add_date"):
                        #     body['bookmark_created'] = int({n.get("add_date")})
                        body['board'] = folder_name
                        item = Item(**body, added_by=user, )
                        item.save()
                        item_id = item.id

                        # if folder_name == "Other Bookmarks":
                        #     print(f'url = {n.get("href")}')
                        #     print(f'website name = {n.text}')
                        #     print(f'add date = {n.get("add_date")}')
                        #     print(f'folder name = {folder_name}')

                items = Item.objects().to_json()
                data = json.dumps(
                    {'id': str(item_id), 'count': len(json.loads(items)), 'message': "Successfully inserted"})
                return Response(data, mimetype="application/json", status=200)


        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise ItemAlreadyExistsError
        except Exception as e:
            print(n.get("tags"))
            print({n.get("text")})
            print(e)
            raise InternalServerError
