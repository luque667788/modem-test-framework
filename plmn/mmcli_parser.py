import re
import json

class MMCLIParser():
    @classmethod
    def save_json(cls, obj, fname):
        with open(fname, 'w') as json_file:
            json.dump(obj, json_file, indent=4)

    @classmethod
    def parse(cls, text):
        # type (str) -> Object
        res = {}
        cur_sys = None
        cur_subsys = None
        lines = text.split('\n')

        for idx in range(0, len(lines)):
            line = lines[idx]
            if '-------------------------' in line:
                cur_sys = None
                cur_subsys = None
                continue

            if '|' not in line:
                continue

            if len(line.strip()) is 0:
                continue

            first_idx = line.find('|')
            if first_idx > 0:
                sys = re.search('([\w\d\s]+)', line[:first_idx]).group(1)
                sys = sys.strip()
                if sys is not '':
                    cur_sys = sys
                    res[cur_sys] = {}

                second_idx = line.find(':')
                if second_idx >= first_idx:
                    subsys = re.search('([\w\d\s]+)', line[first_idx:second_idx]).group(1)
                    subsys = subsys.strip()
                    if subsys is not '':
                        cur_subsys = subsys
                        res[cur_sys][cur_subsys] = ''

                    val = line[second_idx:].strip().strip(':').strip().strip('\'').strip()
                    res[cur_sys][cur_subsys] = val

                elif second_idx == -1:
                    val = line.strip().strip('\'').strip('|').strip()
                    if val is not '':
                        res[cur_sys][cur_subsys] = res[cur_sys][cur_subsys] + ', ' + val

        return res

    @classmethod
    def parse_keyvalue(cls, text):
        # Parse `mmcli -K` output (dotted-key flat format) into nested dict
        # shaped like legacy MMCLIParser.parse output, so existing consumers
        # (res["Status"]["state"], res["3GPP"]["enabled locks"], ...) keep working.
        flat = {}
        arrays = {}  # base -> list of values, for .length / .value[i]
        for raw in text.split('\n'):
            if ':' not in raw:
                continue
            k, _, v = raw.partition(':')
            k = k.strip()
            v = v.strip()
            m = re.match(r'^(.*)\.value\[(\d+)\]$', k)
            if m:
                base, idx = m.group(1), int(m.group(2))
                arrays.setdefault(base, {})[idx] = v
                continue
            if k.endswith('.length'):
                continue
            flat[k] = v

        def arr_join(base, empty='none'):
            vals = arrays.get(base)
            if not vals:
                return empty
            return ', '.join(vals[i] for i in sorted(vals.keys()))

        res = {'Status': {}, '3GPP': {}, 'SIM': {}, 'Modes': {}, 'Hardware': {}, 'System': {}, 'General': {}}

        # Status section
        if 'modem.generic.state' in flat:
            res['Status']['state'] = flat['modem.generic.state']
        if 'modem.generic.unlock-required' in flat:
            res['Status']['lock'] = flat['modem.generic.unlock-required']
        if 'modem.generic.power-state' in flat:
            res['Status']['power state'] = flat['modem.generic.power-state']
        access = arr_join('modem.generic.access-technologies', empty='')
        if access:
            res['Status']['access tech'] = access
        if 'modem.generic.signal-quality.value' in flat:
            res['Status']['signal quality'] = flat['modem.generic.signal-quality.value']

        # 3GPP section
        if 'modem.3gpp.registration-state' in flat:
            res['3GPP']['registration'] = flat['modem.3gpp.registration-state']
        res['3GPP']['enabled locks'] = arr_join('modem.3gpp.enabled-locks', empty='none')
        if 'modem.3gpp.operator-code' in flat:
            res['3GPP']['operator id'] = flat['modem.3gpp.operator-code']
        if 'modem.3gpp.operator-name' in flat:
            res['3GPP']['operator name'] = flat['modem.3gpp.operator-name']
        if 'modem.3gpp.imei' in flat:
            res['3GPP']['imei'] = flat['modem.3gpp.imei']
        if 'modem.3gpp.packet-service-state' in flat:
            res['3GPP']['packet service state'] = flat['modem.3gpp.packet-service-state']

        # SIM section: signal presence via primary sim path
        sim_path = flat.get('modem.generic.sim')
        if sim_path and sim_path != '--':
            res['SIM']['primary sim path'] = sim_path

        # Hardware / General passthrough (best-effort, for debug/info dumps)
        for src, (sec, key) in {
            'modem.generic.manufacturer': ('Hardware', 'manufacturer'),
            'modem.generic.model': ('Hardware', 'model'),
            'modem.generic.revision': ('Hardware', 'firmware revision'),
            'modem.generic.equipment-identifier': ('Hardware', 'equipment id'),
            'modem.generic.device-identifier': ('General', 'device id'),
            'modem.dbus-path': ('General', 'path'),
            'modem.generic.plugin': ('System', 'plugin'),
            'modem.generic.primary-port': ('System', 'primary port'),
            'modem.generic.device': ('System', 'device'),
            'modem.generic.current-modes': ('Modes', 'current'),
        }.items():
            if src in flat:
                res[sec][key] = flat[src]

        return res


if __name__ == '__main__':
    text = '''
    
  -------------------------
  Hardware |   manufacturer: 'Sierra Wireless, Incorporated'
           |          model: 'MC7354'
           |       revision: 'SWI9X15C_05.05.58.00 r27038 carmd-fwbuild1 2015/03/04 21:30:23'
           |      supported: 'gsm-umts
           |                  cdma-evdo
           |                  lte
           |                  cdma-evdo, gsm-umts
           |                  gsm-umts, lte
           |                  cdma-evdo, lte
           |                  cdma-evdo, gsm-umts, lte'
           |        current: 'gsm-umts, lte'
           |   equipment id: '359225050108901'
  -------------------------
  System   |         device: '/sys/devices/pci0000:00/0000:00:14.0/usb1/1-3'
           |        drivers: 'option1, qmi_wwan'
           |         plugin: 'Sierra'
           |   primary port: 'cdc-wdm0'
           |          ports: 'ttyUSB2 (at), cdc-wdm0 (qmi), cdc-wdm1 (qmi), wwan1 (net), wwan0 (net)'
  -------------------------
  Numbers  |           own : '13035708302'
  -------------------------
  Status   |           lock: 'sim-pin2'
           | unlock retries: 'sim-pin (3), sim-pin2 (3), sim-puk (10), sim-puk2 (10)'
           |          state: 'registered'
           |    power state: 'on'
           |    access tech: 'lte'
           | signal quality: '59' (recent)
  -------------------------
  Modes    |      supported: 'allowed: 2g, 3g, 4g; preferred: none'
           |        current: 'allowed: 2g, 3g, 4g; preferred: none'
  -------------------------
  Bands    |      supported: 'cdma-bc0-cellular-800, cdma-bc1-pcs-1900, cdma-bc10-secondary-800, cdma-bc15-aws, dcs, egsm, pcs, g850, u2100, u1900, u17iv, u850, u900, eutran-ii, eutran-iv, eutran-v, eutran-xiii, eutran-xvii, eutran-xxv'
           |        current: 'cdma-bc15-aws, dcs, egsm, pcs, g850, u2100, u1900, u850, u900, eutran-ii, eutran-iv, eutran-v, eutran-xvii'
  -------------------------
  IP       |      supported: 'ipv4, ipv6, ipv4v6'
  -------------------------
  3GPP     |           imei: '359225050108901'
           |  enabled locks: 'none'
           |    operator id: '310410'
           |  operator name: 'AT&T'
    
    '''

    # Parse text and save as out.json
    res = MMCLIParser.parse(text)
    MMCLIParser.save_json(res, 'out.json')

