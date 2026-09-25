from datetime import UTC, datetime

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models import Integration, Organization, Repository


@pytest.mark.anyio
async def test_installation_exclusive_and_repository_tenant_foreign_key(engine):
    async with async_sessionmaker(engine, expire_on_commit=False)() as session:
        first = Organization(name="First", slug="first")
        second = Organization(name="Second", slug="second")
        session.add_all([first, second])
        await session.flush()
        integration = Integration(
            organization_id=first.id,
            app_id=1,
            installation_id=2,
            account_id=3,
            account_login="team",
        )
        session.add(integration)
        await session.flush()
        with pytest.raises(IntegrityError), session.no_autoflush:
            async with session.begin_nested():
                session.add(
                    Integration(
                        organization_id=second.id,
                        app_id=1,
                        installation_id=2,
                        account_id=3,
                        account_login="team",
                    )
                )
                await session.flush()
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(
                    Repository(
                        organization_id=second.id,
                        integration_id=integration.id,
                        external_id=99,
                        full_name="team/api",
                        private=True,
                        catalog_refreshed_at=datetime.now(UTC),
                    )
                )
                await session.flush()
        repository = Repository(
            organization_id=first.id,
            integration_id=integration.id,
            external_id=99,
            full_name="team/api",
            private=True,
            catalog_refreshed_at=datetime.now(UTC),
        )
        session.add(repository)
        await session.flush()
        assert repository.selected is False
        original_id = repository.id
        repository.full_name = "team/renamed"
        await session.flush()
        assert repository.id == original_id
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(
                    Repository(
                        organization_id=first.id,
                        integration_id=integration.id,
                        external_id=99,
                        full_name="team/duplicate",
                        private=True,
                        catalog_refreshed_at=datetime.now(UTC),
                    )
                )
                await session.flush()
        integration.status = "suspended"
        await session.flush()
        with pytest.raises(IntegrityError):
            async with session.begin_nested():
                session.add(
                    Integration(
                        organization_id=second.id,
                        app_id=1,
                        installation_id=2,
                        account_id=3,
                        account_login="team",
                    )
                )
                await session.flush()
        integration.status = "disconnected"
        await session.flush()
        session.add(
            Integration(
                organization_id=second.id,
                app_id=1,
                installation_id=2,
                account_id=3,
                account_login="team",
            )
        )
        await session.flush()
        assert repository.organization_id == first.id
