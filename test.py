from pysim900a import SIM900A
import logging
import time

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sim = SIM900A("/dev/ttyUSB0")

print(sim.get_sim_status())
print(sim.get_provider_name())
# sim.send_message("0901484041", "bonjour mon ami")
# sim.delete_all_sms()
sms = sim.read_all_sms()
for s in sms:
    print(s)