#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔════════════════════════════════════════════════════╗
║                YUCELSAN - DEVOPS LAB               ║
╠════════════════════════════════════════════════════╣
║ 📌 Script Name   : ./backend/services/zabbix_service.py     
║ 🧑 Author        : Serdar AYSAN                   
║ 🌐 Website       : https://www.yucelsan.fr         
║ 📧 Contact       : contact@yucelsan.fr             
║ ⚙️ Version       : 1.0.0                         
║ 📦 Dependencies  : <requests, fastapi, etc.>       
║ 🖥️ Environment   : Linux / Docker / Kubernetes   
╠════════════════════════════════════════════════════
║ 🚀 Usage:                                                 
║     /opt/infraRocket/venv/bin/python -m uvicorn /   
║      backend.main:app --host 0.0.0.0 --port 8001            
╠════════════════════════════════════════════════════
║ 🔐 License: MIT / Private / YUCELSAN             
╚════════════════════════════════════════════════════
"""

import re
import requests
import urllib3
from datetime import datetime
from backend.core.config import settings

if not settings.ZABBIX_VERIFY_SSL:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ZabbixService:
    def __init__(self):
        self.url = settings.ZABBIX_URL
        self.token = settings.ZABBIX_API_TOKEN
        self.verify_ssl = settings.ZABBIX_VERIFY_SSL

    def _request(self, method: str, params: dict):
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": 1
        }

        headers = {
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {self.token}"
        }

        response = requests.post(
            self.url,
            json=payload,
            headers=headers,
            timeout=20,
            verify=self.verify_ssl
        )
        response.raise_for_status()

        data = response.json()
        if "error" in data:
            raise Exception(f"Zabbix API error: {data['error']}")

        return data["result"]

    def get_problem_count(self, severities=None):
        params = {
            "output": "extend",
            "recent": True
        }
        if severities:
            params["severities"] = severities

        result = self._request("problem.get", params)
        return len(result)

    def get_down_hosts_count(self):
        result = self._request(
            "host.get",
            {
                "output": ["host"],
                "selectInterfaces": ["available"],
                "monitored_hosts": True
            }
        )

        down = 0
        for host in result:
            interfaces = host.get("interfaces", [])
            if interfaces and all(str(i.get("available")) == "2" for i in interfaces):
                down += 1
        return down

    def get_dashboard_summary(self):
        return {
            "critical_alerts": self.get_problem_count([4, 5]),
            "down_hosts": self.get_down_hosts_count(),
            "last_sync": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

    def get_network_hosts(self):
        return self._request(
            "host.get",
            {
                "output": ["hostid", "host", "name", "status"],
                "selectInterfaces": ["interfaceid", "ip", "dns", "port", "available", "type"],
                "selectInventory": ["type", "name", "site_address_a", "location", "model", "vendor", "asset_tag"],
                "selectGroups": ["groupid", "name"],
                "monitored_hosts": True
            }
        )

    def get_active_problems(self):
        return self._request(
            "problem.get",
            {
                "output": "extend",
                "selectTags": "extend",
                "recent": True,
                "sortfield": ["eventid"],
                "sortorder": "DESC"
            }
        )

    def get_items_for_hosts(self, hostids):
        if not hostids:
            return []

        return self._request(
            "item.get",
            {
                "output": ["itemid", "hostid", "name", "key_", "lastvalue", "units", "value_type"],
                "hostids": hostids,
                "webitems": True,
                "sortfield": "name",
                "filter": {
                    "status": "0"
                }
            }
        )

    def _detect_tech_group(self, host, host_type):
        name = (host.get("name") or host.get("host") or "").lower()
        groups = " ".join(g.get("name", "") for g in host.get("groups", [])).lower()
        inventory = host.get("inventory") or {}
        model = (inventory.get("model") or "").lower()
        vendor = (inventory.get("vendor") or "").lower()

        text = f"{name} {groups} {model} {vendor}"

        if host_type in ["switch", "router"]:
            return "network"

        if host_type == "firewall":
            return "security"

        if any(x in text for x in ["vmware", "esxi", "vcenter", "vsphere", "hyper-v", "xen"]):
            return "virtualization"

        if host_type == "storage" or any(x in text for x in ["netapp", "san", "nas", "storage"]):
            return "storage"

        if any(x in text for x in [
            "sql", "exchange", "wsus", "backup", "veeam", "monitoring",
                "zabbix", "ldap", "ad", "domain controller", "radius", "lic", "dc0", "dc1"
        ]):
            return "services"

        if host_type == "server":
            return "servers"

        if any(x in text for x in ["wifi", "ap ", "wireless", "printer", "imprimante", "poste", "pc"]):
            return "access"

        return "devices"


    def _group_label(self, tech_group):
        labels = {
            "network": "Réseau",
            "security": "Sécurité",
            "virtualization": "Virtualisation",
            "servers": "Serveurs",
            "storage": "Stockage",
            "services": "Services",
            "devices": "Équipements"
        }
        return labels.get(tech_group, tech_group)

    def _equipment_icon(self, host_type, tech_group, label):
        text = f"{host_type} {tech_group} {label}".lower()

        if "wifi" in text or "wireless" in text or "ap " in text:
            return "wifi"
        if "printer" in text or "imprimante" in text:
            return "printer"
        if "vmware" in text or "esxi" in text or "vcenter" in text or tech_group == "virtualization":
            return "vmware"
        if host_type == "switch":
            return "switch"
        if host_type == "router":
            return "router"
        if host_type == "firewall":
            return "firewall"
        if host_type == "storage":
            return "storage"
        if "pc" in text or "poste" in text or "workstation" in text:
            return "pc"
        return "server"

    def _short_label(self, label, max_len=22):
        if not label:
            return "-"
        return label if len(label) <= max_len else f"{label[:max_len]}..."


    def _site_slug(self, site):
        value = (site or "default-site").strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or "default-site"

    def _slugify(self, value: str) -> str:
        value = (value or "").strip().lower()
        value = re.sub(r"[^a-z0-9]+", "-", value)
        value = re.sub(r"-+", "-", value).strip("-")
        return value or "default"

    def _build_grouped_edges(self, equipment_nodes):
        """
        Liens pragmatiques mais plus lisibles :
        - security -> network
        - network -> virtualization / servers / storage / services / devices
        Répartition par site.
        """
        edges = []
        edge_idx = 1

        by_site = {}
        for node in equipment_nodes:
            site = node["data"]["site"]
            tech_group = node["data"]["tech_group"]
            by_site.setdefault(site, {}).setdefault(tech_group, []).append(node)

        def connect_many(sources, targets, label):
            nonlocal edge_idx
            if not sources or not targets:
                return

            for idx, target in enumerate(targets):
                source = sources[idx % len(sources)]
                edge_status = "down" if (
                    source["data"]["status"] == "down" or target["data"]["status"] == "down"
                ) else "up"

                edges.append({
                    "data": {
                        "id": f"edge_{edge_idx}",
                        "source": source["data"]["id"],
                        "target": target["data"]["id"],
                        "status": edge_status,
                        "label": label
                    }
                })
                edge_idx += 1

        for site, groups in by_site.items():
            security = groups.get("security", [])
            network = groups.get("network", [])
            virtualization = groups.get("virtualization", [])
            servers = groups.get("servers", [])
            storage = groups.get("storage", [])
            services = groups.get("services", [])
            devices = groups.get("devices", [])

            if security and network:
                connect_many(security, network, "security")

            connect_many(network or security, virtualization, "virt")
            connect_many(network or security, servers, "srv")
            connect_many(network or security, storage, "storage")
            connect_many(network or security, services, "svc")
            connect_many(network or security, devices, "access")

        return edges

    def _detect_host_type(self, host):
        name = (host.get("name") or host.get("host") or "").lower()
        groups = " ".join(g.get("name", "") for g in host.get("groups", [])).lower()
        inventory = host.get("inventory") or {}
        inv_type = (inventory.get("type") or "").lower()

        text = f"{name} {groups} {inv_type}"

        if any(x in text for x in ["fortigate", "fortinet", "sonicwall", "firewall", "asa", "pfsense"]):
            return "firewall"
        if any(x in text for x in ["router", "asr", "isr", "wan"]):
            return "router"
        if any(x in text for x in ["switch", "nexus", "aruba", "cisco catalyst", "hp procurve"]):
            return "switch"
        if any(x in text for x in ["vmware", "esxi", "hyper-v", "xen", "server", "windows", "linux"]):
            return "server"
        if any(x in text for x in ["netapp", "nas", "storage", "san"]):
            return "storage"

        return "device"

    def _extract_site(self, host):
        inventory = host.get("inventory") or {}
        groups = [g.get("name", "") for g in host.get("groups", [])]

        for value in [
            inventory.get("location"),
            inventory.get("site_address_a"),
            *groups
        ]:
            if value and str(value).strip():
                return str(value).strip()

        return "Default Site"

    def _compute_host_status(self, host, host_problems):
        interfaces = host.get("interfaces", [])
        all_down = interfaces and all(str(i.get("available")) == "2" for i in interfaces)
        if all_down:
            return "down"
        if host_problems:
            return "warning"
        return "up"

    def _safe_float(self, value):
        try:
            return float(value)
        except Exception:
            return None

    def _is_temperature_item(self, item_name, item_key):
        text = f"{item_name} {item_key}".lower()
        return any(x in text for x in ["temp", "temperature"])

    def _is_interface_status_item(self, item_name, item_key):
        text = f"{item_name} {item_key}".lower()
        return (
            "ifoperstatus" in text
            or "net.if.status" in text
            or "interface" in text and "status" in text
            or "port" in text and "status" in text
        )

    def _extract_port_name(self, item_name, item_key):
        patterns = [
            r"Interface\s+([A-Za-z0-9\/\-\._]+)",
            r"Port\s+([A-Za-z0-9\/\-\._]+)",
            r"ifDescr\[(.*?)\]",
            r"net\.if\.(?:status|in|out)\[(.*?)\]",
            r"ifOperStatus\[(.*?)\]",
        ]

        for pattern in patterns:
            match = re.search(pattern, item_name, re.IGNORECASE) or re.search(pattern, item_key, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return item_name[:80]

    def _build_items_index(self, items):
        temp_by_host = {}
        interfaces_by_host = {}

        for item in items:
            hostid = str(item["hostid"])
            name = item.get("name", "")
            key_ = item.get("key_", "")
            lastvalue = item.get("lastvalue", "")
            units = item.get("units", "")

            if self._is_temperature_item(name, key_):
                value = self._safe_float(lastvalue)
                if value is not None:
                    current = temp_by_host.get(hostid)
                    if current is None or value > current["value"]:
                        temp_by_host[hostid] = {
                            "value": value,
                            "label": f"{value}{units}" if units else str(value),
                            "name": name
                        }

            if self._is_interface_status_item(name, key_):
                port_name = self._extract_port_name(name, key_)
                port_status = "unknown"

                if str(lastvalue) in ["1", "up", "UP"]:
                    port_status = "up"
                elif str(lastvalue) in ["2", "0", "down", "DOWN"]:
                    port_status = "down"

                interfaces_by_host.setdefault(hostid, []).append({
                    "itemid": item["itemid"],
                    "name": name,
                    "key": key_,
                    "port_name": port_name,
                    "status": port_status,
                    "raw_value": lastvalue
                })

        return temp_by_host, interfaces_by_host

    def _build_realistic_edges(self, nodes):
        """
        V2 pragmatique :
        - firewall -> router
        - router -> switch
        - switch -> server/storage/device
        Sans fake 'pivot unique'
        """
        by_type = {}
        for node in nodes:
            by_type.setdefault(node["data"]["type"], []).append(node)

        edges = []
        edge_idx = 1

        def connect_many(sources, targets, label):
            nonlocal edge_idx
            if not sources or not targets:
                return

            # répartition simple pour éviter l'effet étoile unique
            for idx, target in enumerate(targets):
                source = sources[idx % len(sources)]
                edge_status = "down" if (
                    source["data"]["status"] == "down" or target["data"]["status"] == "down"
                ) else "up"

                edges.append({
                    "data": {
                        "id": f"edge_{edge_idx}",
                        "source": source["data"]["id"],
                        "target": target["data"]["id"],
                        "status": edge_status,
                        "label": label
                    }
                })
                edge_idx += 1

        connect_many(by_type.get("firewall", []), by_type.get("router", []), "WAN")
        connect_many(
            by_type.get("router", []) or by_type.get("firewall", []),
            by_type.get("switch", []),
            "uplink"
        )
        connect_many(
            by_type.get("switch", []),
            by_type.get("server", []) + by_type.get("storage", []) + by_type.get("device", []),
            "access"
        )

        return edges

    def _build_synoptic_positions(self, equipments):
        """
        Placement synoptique multi-rangées pour éviter les mini-icônes tassées.
        """
        lane_cfg = {
            "security": {"y": 120, "x_start": 180, "x_gap": 260, "row_gap": 180, "per_row": 6},
            "network": {"y": 300, "x_start": 220, "x_gap": 240, "row_gap": 180, "per_row": 6},
            "virtualization": {"y": 520, "x_start": 120, "x_gap": 240, "row_gap": 180, "per_row": 4},
            "storage": {"y": 520, "x_start": 760, "x_gap": 240, "row_gap": 180, "per_row": 4},
            "servers": {"y": 520, "x_start": 1320, "x_gap": 230, "row_gap": 180, "per_row": 5},
            "services": {"y": 820, "x_start": 340, "x_gap": 230, "row_gap": 180, "per_row": 6},
            "access": {"y": 1120, "x_start": 160, "x_gap": 210, "row_gap": 180, "per_row": 8},
            "devices": {"y": 1120, "x_start": 160, "x_gap": 210, "row_gap": 180, "per_row": 8},
        }

        counts = {k: 0 for k in lane_cfg.keys()}
        positioned = []

        network_nodes = [e for e in equipments if e["tech_group"] == "network"]
        net_count = len(network_nodes)

        for eq in equipments:
            group = eq["tech_group"]
            cfg = lane_cfg.get(group, lane_cfg["devices"])
            idx = counts.get(group, 0)

            if group == "network" and net_count > 0:
                row = idx // cfg["per_row"]
                col = idx % cfg["per_row"]
                total_in_first_row = min(net_count, cfg["per_row"])
                total_width = (total_in_first_row - 1) * cfg["x_gap"]
                center_x = 1100
                x = center_x - (total_width / 2) + (col * cfg["x_gap"])
                y = cfg["y"] + (row * cfg["row_gap"])
            else:
                row = idx // cfg["per_row"]
                col = idx % cfg["per_row"]
                x = cfg["x_start"] + (col * cfg["x_gap"])
                y = cfg["y"] + (row * cfg["row_gap"])

            counts[group] = idx + 1
            eq["position"] = {"x": int(x), "y": int(y)}
            positioned.append(eq)

        return positioned


    def build_topology(self, site_filter: str | None = None):
        hosts = self.get_network_hosts()
        hostids = [h["hostid"] for h in hosts]

        items = self.get_items_for_hosts(hostids)
        problems = self.get_active_problems()

        temp_by_host, interfaces_by_host = self._build_items_index(items)

        problems_by_host = {}
        for p in problems:
            hostid = p.get("objectid")
            if hostid:
                problems_by_host.setdefault(str(hostid), []).append(p)

        sites = {}
        counters = {}

        for host in hosts:
            hostid = str(host["hostid"])
            host_type = self._detect_host_type(host)
            tech_group = self._detect_tech_group(host, host_type)
            site = self._extract_site(host)
            site_slug = self._slugify(site)

            if site_filter and site_slug != site_filter:
                continue

            host_problems = problems_by_host.get(hostid, [])
            status = self._compute_host_status(host, host_problems)
            inventory = host.get("inventory") or {}
            interfaces = host.get("interfaces", [])
            temp = temp_by_host.get(hostid)
            ports = interfaces_by_host.get(hostid, [])
            ports_down = [p for p in ports if p["status"] == "down"]

            main_ip = "-"
            if interfaces:
                main_ip = interfaces[0].get("ip") or interfaces[0].get("dns") or "-"

            label = host.get("name") or host.get("host") or f"host-{hostid}"

            equipment = {
                "id": f"host_{hostid}",
                "hostid": hostid,
                "label": label,
                "short_label": self._short_label(label, 20),
                "type": host_type,
                "tech_group": tech_group,
                "status": status,
                "site": site,
                "site_slug": site_slug,
                "ip": main_ip,
                "temperature": temp["value"] if temp else None,
                "temperature_label": temp["label"] if temp else "N/A",
                "problems_count": len(host_problems),
                "ports_count": len(ports),
                "ports_down_count": len(ports_down),
                "vendor": inventory.get("vendor") or "",
                "model": inventory.get("model") or "",
                "asset_tag": inventory.get("asset_tag") or "",
                "problem_titles": [p.get("name", "") for p in host_problems[:8]],
                "ports_preview": ports[:20],
                "icon": self._equipment_icon(host_type, tech_group, label),
            }

            sites.setdefault(site_slug, {
                "name": site,
                "slug": site_slug,
                "equipments": []
            })
            sites[site_slug]["equipments"].append(equipment)

            counters.setdefault(host_type, 0)
            counters[host_type] += 1

        structured_sites = []
        for site_slug in sorted(sites.keys()):
            site_data = sites[site_slug]
            equipments = sorted(
                site_data["equipments"],
                key=lambda e: (
                    ["security", "network", "virtualization", "storage", "servers", "services", "access", "devices"].index(e["tech_group"])
                    if e["tech_group"] in ["security", "network", "virtualization", "storage", "servers", "services", "access", "devices"]
                    else 99,
                    e["label"].lower()
                )
            )

            equipments = self._build_synoptic_positions(equipments)

            # liens synoptiques pragmatiques
            security_nodes = [e for e in equipments if e["tech_group"] == "security"]
            network_nodes = [e for e in equipments if e["tech_group"] == "network"]
            virt_nodes = [e for e in equipments if e["tech_group"] == "virtualization"]
            storage_nodes = [e for e in equipments if e["tech_group"] == "storage"]
            server_nodes = [e for e in equipments if e["tech_group"] == "servers"]
            service_nodes = [e for e in equipments if e["tech_group"] == "services"]
            access_nodes = [e for e in equipments if e["tech_group"] in ["access", "devices"]]

            def mk_edge(idx, source, target, label):
                down = (
                    source["status"] == "down"
                    or target["status"] == "down"
                    or source["ports_down_count"] > 0
                    or target["ports_down_count"] > 0
                )
                return {
                    "id": f"{site_slug}_edge_{idx}",
                    "source": source["id"],
                    "target": target["id"],
                    "label": label,
                    "status": "down" if down else "up",
                    "source_label": source["label"],
                    "target_label": target["label"],
                    "source_port": source["ports_preview"][0]["port_name"] if source["ports_preview"] else "N/A",
                    "target_port": target["ports_preview"][0]["port_name"] if target["ports_preview"] else "N/A",
                    "source_ports_down": source["ports_down_count"],
                    "target_ports_down": target["ports_down_count"],
                }

            edges = []
            edge_idx = 1

            def connect_many(sources, targets, label):
                nonlocal edge_idx
                if not sources or not targets:
                    return
                for idx, target in enumerate(targets):
                    source = sources[idx % len(sources)]
                    edges.append(mk_edge(edge_idx, source, target, label))
                    edge_idx += 1

            if security_nodes and network_nodes:
                connect_many(security_nodes, network_nodes, "WAN / Sécurité")

            connect_many(network_nodes or security_nodes, virt_nodes, "Virtualisation")
            connect_many(network_nodes or security_nodes, storage_nodes, "Stockage")
            connect_many(network_nodes or security_nodes, server_nodes, "Serveurs")
            connect_many(network_nodes or security_nodes, service_nodes, "Services")
            connect_many(network_nodes or security_nodes, access_nodes[:24], "Accès")

            structured_sites.append({
                "name": site_data["name"],
                "slug": site_data["slug"],
                "equipments": equipments,
                "edges": edges
            })

        total_hosts = sum(len(site["equipments"]) for site in structured_sites)
        total_links = sum(len(site["edges"]) for site in structured_sites)

        return {
            "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "sites": structured_sites,
            "stats": {
                "total_hosts": total_hosts,
                "total_links": total_links,
                "sites": len(structured_sites),
                "by_type": counters
            }
        }

