from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException
import logging

class RateLimiter:
    """Simple in-memory rate limiter that tracks requests per IP per minute."""
    
    def __init__(self, max_requests: int = 30):
        self.max_requests = max_requests
        self.requests = defaultdict(list)  # IP -> list of request timestamps
        self.last_cleanup = datetime.now()
    
    def is_allowed(self, client_ip: str) -> bool:
        """Check if a request from the given IP is allowed."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean up old requests for this IP
        self.requests[client_ip] = [
            timestamp for timestamp in self.requests[client_ip]
            if timestamp > one_minute_ago
        ]
        
        # Periodically cleanup old IP entries (every 5 minutes)
        if (now - self.last_cleanup).total_seconds() > 300:
            self._cleanup_old_entries()
            self.last_cleanup = now
        
        # Check if under limit
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_ip].append(now)
        return True
    
    def _cleanup_old_entries(self):
        """Remove entries for IPs that haven't made requests recently (internal method)."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        ips_to_remove = []
        for ip, timestamps in list(self.requests.items()):
            # Remove old timestamps
            self.requests[ip] = [ts for ts in timestamps if ts > one_minute_ago]
            # Mark for removal if no recent requests
            if not self.requests[ip]:
                ips_to_remove.append(ip)
        
        for ip in ips_to_remove:
            del self.requests[ip]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
rate_limiter = RateLimiter(max_requests=30)
    
async def check_rate_limit(request: Request):
    """Dependency to check rate limit for incoming requests."""
    client_ip = request.client.host if request.client else "unknown"
    
    if not rate_limiter.is_allowed(client_ip):
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 30 requests per minute allowed."
        )