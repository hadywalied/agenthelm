"""Tests for MemoryHub and MemoryContext."""

import pytest

from agenthelm.memory import MemoryHub, MemoryContext, InMemoryShortTermMemory


class TestMemoryHub:
    """Tests for MemoryHub unified interface."""

    def test_default_creates_in_memory(self):
        """Test that MemoryHub() creates in-memory backends."""
        hub = MemoryHub()
        assert isinstance(hub.short_term, InMemoryShortTermMemory)

    def test_lazy_initialization(self):
        """Test that backends are not created until accessed."""
        hub = MemoryHub()
        # Backends shouldn't be created yet
        assert hub._short_term is None
        assert hub._semantic is None
        # Now they should be created
        _ = hub.short_term
        assert hub._short_term is not None

    @pytest.mark.asyncio
    async def test_short_term_operations(self):
        """Test short-term memory via hub."""
        hub = MemoryHub()
        await hub.short_term.set("key", "value")
        result = await hub.short_term.get("key")
        assert result == "value"

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager."""
        async with MemoryHub() as hub:
            await hub.short_term.set("key", "value")
            assert await hub.short_term.get("key") == "value"

    def test_local_mode_with_data_dir(self, tmp_path):
        """Test that data_dir enables local persistence."""
        hub = MemoryHub(data_dir=tmp_path)
        # Access short_term to trigger creation
        _ = hub.short_term
        # Should have created the SQLite database
        db_file = tmp_path / "short_term.db"
        assert db_file.exists()


class TestMemoryContext:
    """Tests for MemoryContext session-scoped interface."""

    @pytest.fixture
    def hub(self):
        """Create a fresh MemoryHub."""
        return MemoryHub()

    @pytest.mark.asyncio
    async def test_session_scoped_keys(self, hub):
        """Test that keys are scoped to session."""
        ctx1 = MemoryContext(hub, session_id="session1", cleanup_on_exit=False)
        ctx2 = MemoryContext(hub, session_id="session2", cleanup_on_exit=False)

        await ctx1.set("key", "value1")
        await ctx2.set("key", "value2")

        # Each session should have its own value
        assert await ctx1.get("key") == "value1"
        assert await ctx2.get("key") == "value2"

    @pytest.mark.asyncio
    async def test_auto_session_id(self, hub):
        """Test that session_id is auto-generated if not provided."""
        ctx = MemoryContext(hub)
        assert ctx.session_id is not None
        assert len(ctx.session_id) > 0

    @pytest.mark.asyncio
    async def test_context_manager_cleanup(self, hub):
        """Test that context manager cleans up on exit."""
        session_id = "test-session"
        async with MemoryContext(hub, session_id=session_id) as ctx:
            await ctx.set("key", "value")
            assert await ctx.get("key") == "value"

        # After exit, key should be cleaned up
        ctx2 = MemoryContext(hub, session_id=session_id, cleanup_on_exit=False)
        assert await ctx2.get("key") is None

    @pytest.mark.asyncio
    async def test_no_cleanup_when_disabled(self, hub):
        """Test cleanup can be disabled."""
        session_id = "persistent-session"
        async with MemoryContext(
            hub, session_id=session_id, cleanup_on_exit=False
        ) as ctx:
            await ctx.set("key", "value")

        # Key should still exist
        ctx2 = MemoryContext(hub, session_id=session_id, cleanup_on_exit=False)
        assert await ctx2.get("key") == "value"

    @pytest.mark.asyncio
    async def test_delete_key(self, hub):
        """Test deleting a key within context."""
        ctx = MemoryContext(hub, cleanup_on_exit=False)
        await ctx.set("key", "value")
        await ctx.delete("key")
        assert await ctx.get("key") is None
