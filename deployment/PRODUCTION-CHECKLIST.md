# Production Deployment Checklist

Use this checklist to ensure all production deployment steps are completed.

## Pre-Deployment

### Environment Setup
- [ ] Copy `deployment/env.example` to `.env`
- [ ] Update all environment variables in `.env`
- [ ] Generate secure `SECRET_KEY` (minimum 32 characters)
- [ ] Set secure database password
- [ ] Set secure Redis password
- [ ] Configure domain name
- [ ] Set up AWS credentials (for backups)
- [ ] Configure email settings (for alerts)

### Infrastructure
- [ ] Provision servers (Application + GPU if needed)
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Configure firewall rules
- [ ] Set up SSH access with keys
- [ ] Harden SSH configuration

## Deployment

### Docker Setup
- [ ] Build Docker images
- [ ] Test Docker Compose locally
- [ ] Configure docker-compose.yml
- [ ] Set up volumes for persistent data
- [ ] Configure network settings

### Database
- [ ] Initialize PostgreSQL
- [ ] Run database migrations
- [ ] Create database indexes
- [ ] Configure connection pooling
- [ ] Set up database backups
- [ ] Test database restore

### Application
- [ ] Deploy backend application
- [ ] Deploy web frontend
- [ ] Configure reverse proxy (Nginx)
- [ ] Set up load balancing
- [ ] Configure CORS settings
- [ ] Test all API endpoints

### Monitoring
- [ ] Set up Prometheus
- [ ] Configure Grafana dashboards
- [ ] Set up alert rules
- [ ] Configure log aggregation
- [ ] Test monitoring endpoints
- [ ] Verify metrics collection

### Security
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Harden SSH
- [ ] Review security headers
- [ ] Set up rate limiting
- [ ] Configure CORS properly
- [ ] Review and restrict access

### Backup & Recovery
- [ ] Set up automated backups
- [ ] Configure backup retention
- [ ] Test backup process
- [ ] Test restore process
- [ ] Document recovery procedures
- [ ] Set up S3 backup (if using)

## Post-Deployment

### Testing
- [ ] Health check endpoints working
- [ ] API endpoints responding
- [ ] Web frontend accessible
- [ ] Database connections working
- [ ] Redis caching working
- [ ] File uploads working
- [ ] Generation jobs processing
- [ ] WebSocket connections working

### Performance
- [ ] Database queries optimized
- [ ] Indexes created
- [ ] Caching configured
- [ ] Connection pooling working
- [ ] GPU optimization enabled (if applicable)
- [ ] Load balancing configured

### Monitoring
- [ ] All services monitored
- [ ] Alerts configured and tested
- [ ] Dashboards accessible
- [ ] Logs being collected
- [ ] Metrics being exported

### Documentation
- [ ] Deployment procedures documented
- [ ] Recovery procedures documented
- [ ] Maintenance procedures documented
- [ ] Runbooks created
- [ ] Contact information updated

## Ongoing Maintenance

### Daily
- [ ] Check service health
- [ ] Review error logs
- [ ] Monitor resource usage
- [ ] Verify backups completed

### Weekly
- [ ] Review performance metrics
- [ ] Check disk space
- [ ] Review security logs
- [ ] Update dependencies (if needed)

### Monthly
- [ ] Security updates
- [ ] Performance review
- [ ] Capacity planning
- [ ] Disaster recovery test
- [ ] Backup integrity check

### Quarterly
- [ ] Full system review
- [ ] Architecture review
- [ ] Security audit
- [ ] Documentation update
- [ ] Disaster recovery drill

## Emergency Contacts

- DevOps Team: [Contact]
- Database Admin: [Contact]
- Security Team: [Contact]
- On-Call Engineer: [Contact]

## Important URLs

- Application: https://yourdomain.com
- API Health: https://yourdomain.com/api/health
- Metrics: https://yourdomain.com/metrics
- Prometheus: http://yourdomain.com:9090
- Grafana: http://yourdomain.com:3001

## Quick Commands

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Run backup
./deployment/scripts/backup_db.sh

# Maintenance check
./deployment/scripts/maintenance_check.sh

# Update application
./deployment/scripts/update_application.sh
```
