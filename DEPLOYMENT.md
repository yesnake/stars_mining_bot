# Production Deployment Checklist

## Pre-deployment

- [ ] Set all environment variables in `.env`
- [ ] Run health check: `python healthcheck.py`
- [ ] Verify database is accessible
- [ ] Test bot token with BotFather
- [ ] Verify Botohub API token

## Database Setup

```bash
# The bot creates tables automatically on startup
# No manual migration needed
```

## Running the Bot

```bash
# Install dependencies
pip install -r requirements.txt

# Run health check
python healthcheck.py

# Start the bot
python main.py
```

## Production Considerations

### Logging
- Logs are written to `bot.log` and console
- Log rotation recommended for production
- Current log level: INFO

### Database
- Connection pooling configured (pool_size=10, max_overflow=20)
- Pool pre-ping enabled for stale connection detection
- Connections recycled every hour
- All datetimes use UTC timezone

### Monitoring
- Miner expiration checked every 5 minutes
- Users are notified when their miner stops
- Failed notifications are logged but don't stop monitoring

### Error Handling
- Global error handler logs all exceptions
- Failed database operations are rolled back
- External API failures (Botohub) fail gracefully

### Security
- All secrets stored in environment variables
- Database uses connection pooling with limits
- Input validation on all user operations
- No SQL injection vulnerabilities

## Common Issues

### Bot not starting
1. Check `.env` file exists with all required variables
2. Run `python healthcheck.py` to diagnose
3. Check database connection string format

### Database connection errors
1. Verify PostgreSQL is running
2. Check connection string format: `postgresql+asyncpg://user:password@host:port/database`
3. Ensure asyncpg driver is installed

### Miner not stopping
- Miners expire after 1 hour
- Monitor checks every 5 minutes
- Check bot.log for errors in monitor loop

## Monitoring Commands

```bash
# Watch logs in real-time
tail -f bot.log

# Check for errors
grep ERROR bot.log

# Check for critical issues
grep CRITICAL bot.log
```
