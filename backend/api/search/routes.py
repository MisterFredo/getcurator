
@router.post("/search")
def search_route(
    request: ContentSearchRequest
):
    try:
        return search_contents(request)

    except Exception as e:
        raise HTTPException(
            400,
            str(e)
        )
