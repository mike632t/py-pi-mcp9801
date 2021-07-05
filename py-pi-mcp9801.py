#!/usr/bin/env python
#
# py-pi-mcp9801
#
# Reads the current temprature a MCP9801/2/3 sensor.
#
# This  program  is free software: you can redistribute it and/or modify  it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your  option)
# any later version.
#
# This  program  is  distributed  in the hope that it will  be  useful,  but
# WITHOUT   ANY   WARRANTY;   without  even   the   implied   warranty    of
# MERCHANTABILITY  or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.py-pi-mcp9801.py
#
# You  should have received a copy of the GNU General Public  License  along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# 04 Jul 21   0.1   - Initial version - MT
#             0.2   - Added comments and unicode degree symbol - MT
#
import time

class MCP9801(object):
  """
      Interface to the MCP9801 temperature sensor.
        :param  _bus:       The I2C bus to use (required).
        :param  _address:   The address of the device (optional).
  """
  # Valid addesses
  MCP9801_VALID_I2C_ADDRESS = [0x4f]    # Valid device addreses

  # Register addresses for raw data
  MCP9801_REG_AMBIENT_TEMP = 0x00       # Ambient tempreature register
  MCP9801_REG_CONFIG = 0x01             # Sensor configuration register
  MCP9801_REG_TEMP_HYST = 0x02          # Temperature hysteresis register
  MCP9801_REG_TEMP_LIMIT = 0x03         # Temperature limit set register
  
  MCP9801_REG_CONFIG_DEFAULT = 0x60     # Use highest resolution 
                                        # Factory default = 0x00
  
  def __init__(self, _bus=None, _address=None):
    if _bus is None: # Check bus if defined 
      raise IOError('I2C bus not specified') 
    else:
      self.bus = _bus

    # Did the user specify an I2C address?
    if _address is None:
      self.address = self.MCP9801_VALID_I2C_ADDRESS[0]  # Use default
    else:
      self.address = _address
    self.reset()

  def reset(self):
    self.bus.write_byte_data(self.address, self.MCP9801_REG_CONFIG, self.MCP9801_REG_CONFIG_DEFAULT)

  @property
  def temperature(self):
    """
        Gets the  current sensor temperature.  The raw data is  held  in the
        upper 12 bits of a 16-bit word retuered as a little-endian value. To
        obtain the current ambient temperature the byte order is swapped and
        the value converted into a float.
    """
    _raw = self.bus.read_word_data(self.address, self.MCP9801_REG_AMBIENT_TEMP)
    _raw  = (((_raw & 0xff) << 8)|((_raw >> 8) & 0xff)) # Swap bytes
    if (_raw & 0x8000): # Check sign bit and convert into a signed integer if set
      _raw = _raw - 0x8000 
    _temperature = _raw / 256.0 # Convert to float
    return _temperature 

  @property
  def resolution(self):
    """
        Gets the current sensor temperature resolution from bits 5 and 6  of
        the configuration register.
        
        Value     Resolution     Response time
          0            0.5 C        30 ms
          1           0.25 C        65 ms
          2          0.125 C       130 ms
          3         0.0625 C       250 ms
    """
    _data = self.bus.read_word_data(self.address, self.MCP9801_REG_CONFIG)
    return _data & 0b01100000 >> 5

  @resolution.setter
  def resolution(self, _mode):
    """
        Saves the temperature resolution in the configuration register. 
    """
    _mode &= 0x03 # Ignore anything bit the least signifigent two bits
    _data = self.bus.read_word_data(self.address, self.MCP9801_REG_CONFIG)
    _data &= 0b10011111 # Clear the mode bits
    _data |= _mode << 5   # Set mode bits
    self.bus.write_byte_data(self.address, self.MCP9801_REG_CONFIG, _data)

if __name__ == '__main__':

  import time, sys
  import smbus

  INTERVAL = 10
  I2CBUS = 1

  try:
    sys.stdout.write ("%s\n" % sys.version.split('\n')[0])
    _bus = smbus.SMBus(I2CBUS)
    _mcp9801 = MCP9801(_bus)
    _mcp9801.resolution = 0x01 # Change resolution to 0.25 degree

    _now = time.time()
    _time = (_now - _now % INTERVAL) + INTERVAL

    while True:
       time.sleep (0.1)
       _now = time.time()
       if _time -_now <= 0:
          _time = (_now - _now % INTERVAL) + INTERVAL
          sys.stdout.write ("%s\t" % time.strftime('%X', (time.localtime(time.time()))))
          # sys.stdout.write ("%.2f°C\n" % round(_mcp9801.temperature, 2))
          sys.stdout.write ((u'%.2f\u00b0C\n' % round(_mcp9801.temperature, 2)).encode('utf-8'))

  except KeyboardInterrupt: # Ctrl-C
    sys.stdout.write("\n")
  #except IOError, (_errno, _errmsg):
  #  raise SystemExit(_errmsg)    
  except Exception: # Catch all other errors - otherwise the script will just fail silently!
    import traceback
    raise SystemExit(traceback.format_exc())
  sys.stdout.flush()
  raise SystemExit 
