from backend.services.zabbix_service import ZabbixService

z = ZabbixService()
print(z.get_dashboard_summary())
