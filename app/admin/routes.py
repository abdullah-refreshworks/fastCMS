"""Admin dashboard routes."""
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.collection import Collection
from app.db.models.file import File
from app.core.security import verify_password
from app.services.collection_service import CollectionService
from app.services.record_service import RecordService
from app.schemas.collection import CollectionCreate, CollectionUpdate
from app.schemas.record import RecordCreate, RecordUpdate
from app.utils.field_types import FieldSchema
import json


router = APIRouter()
templates = Jinja2Templates(directory="app/admin/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Show login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle login."""
    # Get user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "error": "Invalid email or password",
            },
        )

    # Create session token and set cookie
    from app.core.security import create_access_token
    from datetime import timedelta

    access_token = create_access_token(
        data={"sub": user.id, "email": user.email},
        expires_delta=timedelta(hours=24),
    )

    response = RedirectResponse("/admin?success=Login successful", status_code=302)
    response.set_cookie(
        key="admin_session",
        value=access_token,
        httponly=True,
        max_age=86400,  # 24 hours
        samesite="lax",
    )
    return response


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    """Show admin dashboard."""
    # Get stats
    collections_count = await db.scalar(select(func.count(Collection.id)))
    users_count = await db.scalar(select(func.count(User.id)))
    files_count = await db.scalar(select(func.count(File.id)).where(File.deleted == False))

    # Get recent collections
    result = await db.execute(
        select(Collection).order_by(Collection.created.desc()).limit(10)
    )
    collections = result.scalars().all()

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "stats": {
                "collections": collections_count or 0,
                "users": users_count or 0,
                "files": files_count or 0,
            },
            "collections": collections,
        },
    )


@router.get("/logout")
async def logout():
    """Handle logout."""
    response = RedirectResponse("/admin/login?success=Logged out successfully", status_code=302)
    # Clear session cookie
    response.delete_cookie(key="admin_session")
    return response


# Collections Management
@router.get("/collections", response_class=HTMLResponse)
async def collections_list(request: Request, db: AsyncSession = Depends(get_db)):
    """Show collections list."""
    result = await db.execute(select(Collection).order_by(Collection.created.desc()))
    collections = result.scalars().all()

    return templates.TemplateResponse(
        "collections.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collections": collections,
        },
    )


@router.get("/collections/new", response_class=HTMLResponse)
async def collection_new(request: Request):
    """Show create collection form."""
    return templates.TemplateResponse(
        "collection_form.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": None,
        },
    )


@router.post("/collections/new")
async def collection_create(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle collection creation."""
    form_data = await request.form()

    # Parse schema fields from form
    schema = []
    field_index = 0
    while f"fields[{field_index}][name]" in form_data:
        field = FieldSchema(
            name=form_data[f"fields[{field_index}][name]"],
            type=form_data[f"fields[{field_index}][type]"],
            required=f"fields[{field_index}][required]" in form_data,
            unique=f"fields[{field_index}][unique]" in form_data,
            options=None,
        )
        schema.append(field)
        field_index += 1

    # Create collection
    collection_service = CollectionService(db)
    collection_data = CollectionCreate(
        name=form_data["name"],
        type=form_data["type"],
        schema=schema,
    )

    try:
        collection = await collection_service.create_collection(collection_data)
        return RedirectResponse(
            f"/admin/collections/{collection.id}?success=Collection created successfully",
            status_code=302,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "collection_form.html",
            {
                "request": request,
                "user": {"email": "admin@example.com"},
                "collection": None,
                "error": f"Failed to create collection: {str(e)}",
            },
        )


@router.get("/collections/{collection_id}", response_class=HTMLResponse)
async def collection_detail(
    request: Request,
    collection_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show collection details."""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    return templates.TemplateResponse(
        "collection_detail.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
        },
    )


@router.get("/collections/{collection_id}/edit", response_class=HTMLResponse)
async def collection_edit(
    request: Request,
    collection_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show edit collection form."""
    result = await db.execute(select(Collection).where(Collection.id == collection_id))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    return templates.TemplateResponse(
        "collection_form.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
        },
    )


@router.post("/collections/{collection_id}/edit")
async def collection_update(
    request: Request,
    collection_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle collection update."""
    form_data = await request.form()

    # Parse schema fields from form
    schema = []
    field_index = 0
    while f"fields[{field_index}][name]" in form_data:
        field = FieldSchema(
            name=form_data[f"fields[{field_index}][name]"],
            type=form_data[f"fields[{field_index}][type]"],
            required=f"fields[{field_index}][required]" in form_data,
            unique=f"fields[{field_index}][unique]" in form_data,
            options=None,
        )
        schema.append(field)
        field_index += 1

    # Update collection
    collection_service = CollectionService(db)
    collection_data = CollectionUpdate(schema=schema)

    try:
        await collection_service.update_collection(collection_id, collection_data)
        return RedirectResponse(
            f"/admin/collections/{collection_id}?success=Collection updated successfully",
            status_code=302,
        )
    except Exception as e:
        result = await db.execute(select(Collection).where(Collection.id == collection_id))
        collection = result.scalar_one_or_none()
        return templates.TemplateResponse(
            "collection_form.html",
            {
                "request": request,
                "user": {"email": "admin@example.com"},
                "collection": collection,
                "error": f"Failed to update collection: {str(e)}",
            },
        )


@router.get("/collections/{collection_id}/delete")
async def collection_delete(
    collection_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle collection deletion."""
    collection_service = CollectionService(db)
    try:
        await collection_service.delete_collection(collection_id)
        return RedirectResponse(
            "/admin/collections?success=Collection deleted successfully",
            status_code=302,
        )
    except Exception as e:
        return RedirectResponse(
            f"/admin/collections?error=Failed to delete collection: {str(e)}",
            status_code=302,
        )


# Records Management
@router.get("/collections/{collection_name}/records", response_class=HTMLResponse)
async def records_list(
    request: Request,
    collection_name: str,
    page: int = 1,
    per_page: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Show records list."""
    # Get collection
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    # Get records
    record_service = RecordService(db, collection_name)
    records_result = await record_service.list_records(
        page=page,
        per_page=per_page,
    )

    return templates.TemplateResponse(
        "records.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
            "records": records_result["items"],
            "total": records_result["total"],
            "page": page,
            "total_pages": records_result["total_pages"],
        },
    )


@router.get("/collections/{collection_name}/records/new", response_class=HTMLResponse)
async def record_new(
    request: Request,
    collection_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Show create record form."""
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    return templates.TemplateResponse(
        "record_form.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
            "record": None,
        },
    )


@router.post("/collections/{collection_name}/records/new")
async def record_create(
    request: Request,
    collection_name: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle record creation."""
    # Get collection
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    # Parse form data
    form_data = await request.form()
    data = {}

    for field in collection.schema:
        field_name = field.name
        if field_name in form_data:
            value = form_data[field_name]

            # Convert value based on field type
            if field.type == "bool":
                data[field_name] = True
            elif field.type == "number":
                data[field_name] = float(value) if value else None
            elif field.type == "json":
                try:
                    data[field_name] = json.loads(value) if value else None
                except json.JSONDecodeError:
                    data[field_name] = value
            else:
                data[field_name] = value if value else None
        elif field.type == "bool":
            # Checkboxes not in form_data means unchecked
            data[field_name] = False

    # Create record
    record_service = RecordService(db, collection_name)
    record_data = RecordCreate(data=data)

    try:
        record = await record_service.create_record(record_data)
        return RedirectResponse(
            f"/admin/collections/{collection_name}/records/{record.id}?success=Record created successfully",
            status_code=302,
        )
    except Exception as e:
        return templates.TemplateResponse(
            "record_form.html",
            {
                "request": request,
                "user": {"email": "admin@example.com"},
                "collection": collection,
                "record": None,
                "error": f"Failed to create record: {str(e)}",
            },
        )


@router.get("/collections/{collection_name}/records/{record_id}", response_class=HTMLResponse)
async def record_detail(
    request: Request,
    collection_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show record details."""
    # Get collection
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    # Get record
    record_service = RecordService(db, collection_name)
    record = await record_service.get_record(record_id)

    if not record:
        return RedirectResponse(f"/admin/collections/{collection_name}/records", status_code=302)

    return templates.TemplateResponse(
        "record_detail.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
            "record": record,
        },
    )


@router.get("/collections/{collection_name}/records/{record_id}/edit", response_class=HTMLResponse)
async def record_edit(
    request: Request,
    collection_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Show edit record form."""
    # Get collection
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    # Get record
    record_service = RecordService(db, collection_name)
    record = await record_service.get_record(record_id)

    if not record:
        return RedirectResponse(f"/admin/collections/{collection_name}/records", status_code=302)

    return templates.TemplateResponse(
        "record_form.html",
        {
            "request": request,
            "user": {"email": "admin@example.com"},  # TODO: Get from session
            "collection": collection,
            "record": record,
        },
    )


@router.post("/collections/{collection_name}/records/{record_id}/edit")
async def record_update(
    request: Request,
    collection_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle record update."""
    # Get collection
    result = await db.execute(select(Collection).where(Collection.name == collection_name))
    collection = result.scalar_one_or_none()

    if not collection:
        return RedirectResponse("/admin/collections", status_code=302)

    # Parse form data
    form_data = await request.form()
    data = {}

    for field in collection.schema:
        field_name = field.name
        if field_name in form_data:
            value = form_data[field_name]

            # Convert value based on field type
            if field.type == "bool":
                data[field_name] = True
            elif field.type == "number":
                data[field_name] = float(value) if value else None
            elif field.type == "json":
                try:
                    data[field_name] = json.loads(value) if value else None
                except json.JSONDecodeError:
                    data[field_name] = value
            else:
                data[field_name] = value if value else None
        elif field.type == "bool":
            data[field_name] = False

    # Update record
    record_service = RecordService(db, collection_name)
    record_data = RecordUpdate(data=data)

    try:
        await record_service.update_record(record_id, record_data)
        return RedirectResponse(
            f"/admin/collections/{collection_name}/records/{record_id}?success=Record updated successfully",
            status_code=302,
        )
    except Exception as e:
        record = await record_service.get_record(record_id)
        return templates.TemplateResponse(
            "record_form.html",
            {
                "request": request,
                "user": {"email": "admin@example.com"},
                "collection": collection,
                "record": record,
                "error": f"Failed to update record: {str(e)}",
            },
        )


@router.get("/collections/{collection_name}/records/{record_id}/delete")
async def record_delete(
    collection_name: str,
    record_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle record deletion."""
    record_service = RecordService(db, collection_name)
    try:
        await record_service.delete_record(record_id)
        return RedirectResponse(
            f"/admin/collections/{collection_name}/records?success=Record deleted successfully",
            status_code=302,
        )
    except Exception as e:
        return RedirectResponse(
            f"/admin/collections/{collection_name}/records?error=Failed to delete record: {str(e)}",
            status_code=302,
        )
