
class CustomException(Exception):
    def __init__(self, status_code:float, detail:str = ""):
        self.status_code = status_code
        self.detail = detail


class APIException(Exception):
    STATUS_DICT = {
        200.0 : "OK",
        204.0 :	"No content",

        400.0 : "Bad request",

        401.0 : "Access denied",
        401.1 : "Logon failed.",
        # .6 : Token / User ERROR
        401.61 : "Not authenticated.",
        401.62 : "Token has expired.",

        403.0 : "Forbidden",
        403.1 : "Execute access forbidden.",
        403.2 : "Read access forbidden.",
        403.3 : "Write access forbidden.",
        403.6 : "Token renewal forbidden.",
        # .7 : order_router ERROR
        403.71 : "Status is already finish.",
        403.72 : "Batch is out of range.",

        404.0 : "Not found",
        # .1 : order_router/report ERROR
        404.11 : "Report Not found about input date",
        404.12 : "Report Not found about input id", 

        405.0 : "Method not allowed",

        409.0 : "Conflict",
        409.1 : "Duplicate ID.",
        409.2 : "Duplicate NAME.",

        422.0 : "Unprocessable Entity",
        # .6 : Token  ERROR
        422.61 : "A_Token mismatch.",
        422.62 : "R_Token mismatch.",

        503.0 : "Service unavailable",
        # .5 : MongDB ERROR
        503.51 : "No DataBase exists.",
        503.52 : "No collection exists.",
        503.53 : "Failed to CREATE new document.",
        503.54 : "Failed to UPDATE document.",
        503.55 : "Failed to READ document.",
        503.56 : "Failed to DELETE document.",
        503.57 : "Modified_count is not 1.",
        # .6 : S3 ERROR
        503.61 : "Failed to UPLOAD to S3.",
        # .7 : utill ERROR
        503.71 : "The id format is not valid. Please check"
    }

    def __init__(self):
        self.DEFAULT_CODE = 500,
        self.DEFAULT_DETAIL = "Internal server error" 

    def get_status(self, ex:CustomException) -> (int, str):
        detail = self.STATUS_DICT.get(ex.status_code)
        if ex.status_code in self.STATUS_DICT:
            if ex.detail != "":
                detail = f'{detail}: {ex.detail}'

            return int(ex.status_code), detail
        return self.DEFAULT_CODE, self.DEFAULT_DETAIL
    
    def get_status_assert(self, ex:AssertionError) -> (int, str):
        if ex.args[0] in self.STATUS_DICT:
            detail = self.STATUS_DICT.get(ex.args[0])

            if detail != '':
                return int(ex.args[0]), detail
        return self.DEFAULT_CODE, self.DEFAULT_DETAIL
    
