class GlusterFSHealthComponent:
    def __init__(self):
        self.volume_status = "Healthy"
        self.peer_status = "Connected"
        self.heal_pending = 0
        self.split_brain = 0

    def get_health_status(self):
        return {
            "volume_status": self.volume_status,
            "peer_status": self.peer_status,
            "heal_pending": self.heal_pending,
            "split_brain": self.split_brain
        }

    def update_health(self, volume_status, peer_status, heal_pending, split_brain):
        self.volume_status = volume_status
        self.peer_status = peer_status
        self.heal_pending = heal_pending
        self.split_brain = split_brain

    def display_health(self):
        health_info = self.get_health_status()
        return health_info
    
    def render(self):
        """Render the GlusterFS health component UI"""
        import streamlit as st
        
        st.header("🗄️ GlusterFS Health Monitor")
        st.write("Monitor GlusterFS cluster health and volume status.")
        
        # Get current health status
        health_status = self.get_health_status()
        
        # Display health metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Volume Status",
                value=health_status["volume_status"],
                delta="✅" if health_status["volume_status"] == "Healthy" else "⚠️"
            )
        
        with col2:
            st.metric(
                label="Peer Status", 
                value=health_status["peer_status"],
                delta="✅" if health_status["peer_status"] == "Connected" else "⚠️"
            )
        
        with col3:
            st.metric(
                label="Heal Pending",
                value=str(health_status["heal_pending"]),
                delta="✅" if health_status["heal_pending"] == 0 else "⚠️"
            )
        
        with col4:
            st.metric(
                label="Split Brain",
                value=str(health_status["split_brain"]),
                delta="✅" if health_status["split_brain"] == 0 else "🚨"
            )
        
        # Health summary
        st.subheader("Health Summary")
        if all([
            health_status["volume_status"] == "Healthy",
            health_status["peer_status"] == "Connected", 
            health_status["heal_pending"] == 0,
            health_status["split_brain"] == 0
        ]):
            st.success("🟢 GlusterFS cluster is healthy")
        else:
            st.warning("🟡 GlusterFS cluster requires attention")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Refresh Status"):
                st.rerun()
        with col2:
            if st.button("Run Health Check"):
                st.info("Health check initiated...")
        with col3:
            if st.button("View Logs"):
                st.info("Opening GlusterFS logs...")