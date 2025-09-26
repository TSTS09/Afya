import subprocess
import re
import time
import platform
import matplotlib.pyplot as plt
import socket
import requests
from typing import Dict, Optional, Tuple


def read_data_from_cmd():
    """Execute the command to get WiFi interface details and return the output."""
    system = platform.system().lower()

    try:
        if system == "windows":
            p = subprocess.Popen("netsh wlan show interfaces",
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.stdout.read().decode('utf-8').strip()  # Changed to utf-8 decoding
            out = out.replace('ÿ', '')
            m = re.findall(
                r'SSID\s*:\s*(.*?)\s*\n.*?Signal\s*:\s*(\d+)%', out, re.DOTALL)
            p.communicate()

        elif system == "linux":
            p = subprocess.Popen(
                "iwconfig", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.stdout.read().decode('utf-8').strip()
            m = re.findall(
                r"ESSID:\"(.*?)\".*?Signal level=(-?\d+) dBm", out, re.DOTALL)
            p.communicate()

        elif system == "darwin":  # macOS
            p = subprocess.Popen(
                "airport -I", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out = p.stdout.read().decode('utf-8').strip()
            m = re.findall(
                r" SSID: (.*?)\n.*?agrCtlRSSI: (-?\d+)", out, re.DOTALL)
            p.communicate()

        else:
            raise EnvironmentError(
                "Unsupported operating system: {}".format(system))

        if not m:
            raise ValueError("No WiFi data found.")

        return m

    except (subprocess.SubprocessError, ValueError, EnvironmentError) as e:
        print(f"Error occurred while fetching WiFi data: {e}")
        return []


def percentage_to_dbm(percentage):
    try:
        PdBm_max = -20
        PdBm_min = -85
        PdBm = PdBm_max - ((PdBm_max - PdBm_min) * (1 - (percentage / 100)))
        return PdBm
    except Exception as e:
        print(f"Error in percentage to dBm conversion: {e}")
        return None


def calculate_distance(P0, Pr, N):
    try:
        distance = 10 ** ((P0 - Pr) / (10 * N))
        return distance
    except Exception as e:
        print(f"Error in distance calculation: {e}")
        return None


def display_signal_strength():
    """Display the SSID and signal strength continuously."""
    try:
        while True:
            signal_data = read_data_from_cmd()
            if signal_data:
                # Reference RSSI at 1 meter, in dBm (example value, replace with measured reference RSSI)
                P0 = -69
                N = 2  # Path-loss exponent (2 for open areas, 3-4 for indoors)
                for ssid, signal in signal_data:
                    rssi = percentage_to_dbm(int(signal))
                    if rssi is None:
                        continue
                    distance = calculate_distance(P0, rssi, N)
                    if distance is None:
                        continue
                    print(
                        f"SSID: {ssid.strip()}, Signal Strength: {signal}%, Distance: {distance}")
            else:
                print("No WiFi data found.")
            time.sleep(2)
    except KeyboardInterrupt:
        print("Monitoring stopped.")
    except Exception as e:
        print(f"An error occurred: {e}")


def plot_signal_strength_over_time():
    """Plot the WiFi signal strength over time."""
    try:
        plt.ion()  # Turn on interactive mode for real-time plotting
        fig, ax = plt.subplots()
        # Set the y-axis limits from 0 to 100% for the signal strength
        ax.set_ylim(0, 100)
        ax.set_title("WiFi Signal Strength Over Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Signal Strength (%)")

        times = []  # List to store time values
        signal_strengths = []  # List to store signal strengths

        start_time = time.time()

        while True:
            signal_data = read_data_from_cmd()
            if signal_data:
                for ssid, signal in signal_data:
                    print(f"SSID: {ssid.strip()}, Signal Strength: {signal}%")
                    signal_strength = int(signal)  # Convert signal to integer
                    elapsed_time = time.time() - start_time  # Calculate elapsed time
                    times.append(elapsed_time)  # Append time
                    # Append signal strength
                    signal_strengths.append(signal_strength)

                    # Update plot
                    ax.clear()
                    ax.set_ylim(0, 100)
                    ax.plot(times, signal_strengths, label=ssid)
                    ax.set_title("WiFi Signal Strength Over Time")
                    ax.set_xlabel("Time (s)")
                    ax.set_ylabel("Signal Strength (%)")
                    ax.legend()
                    plt.draw()
                    plt.pause(1)  # Pause for a short period to update the plot
            else:
                print("No WiFi data found.")
            time.sleep(0.001)
    except KeyboardInterrupt:
        print("An error occurred.")
        plt.ioff()  # Turn off interactive mode
        plt.show()
    except Exception as e:
        print(f"Error occurred while plotting: {e}")


def all_Networks():
    try:
        system = platform.system().lower()

        if system == "windows":
            p = subprocess.Popen(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        elif system == "linux":
            p = subprocess.Popen(
                ["nmcli", "-f", "SSID,SIGNAL", "dev", "wifi"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        elif system == "darwin":  # macOS
            p = subprocess.Popen(
                ["airport", "-s"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        out, err = p.communicate()
        out = out.decode('utf-8', errors='ignore').strip()

        if system == "windows":
            networks = re.findall(
                r"SSID\s*\d+\s*:\s*(.*?)\s*\n.*?Signal\s*:\s*(\d+)", out, re.DOTALL)
        elif system == "linux":
            networks = re.findall(r"(\S+)\s+(\d+)", out)
        elif system == "darwin":
            networks = re.findall(r"(\S+)\s+(\d+)", out)

        if not networks:
            raise ValueError("No WiFi networks found.")

        return networks
    except (subprocess.SubprocessError, ValueError) as e:
        print(f"Error occurred while fetching network data: {e}")
        return []


def discover_wifi_networks():
    """Discover and display all active WiFi networks."""
    try:
        networks = all_Networks()
        if networks:
            # Reference RSSI at 1 meter, in dBm (example value, replace with measured reference RSSI)
            P0 = -69
            N = 2  # Path-loss exponent (2 for open areas, 3-4 for indoors)
            print("Available WiFi Networks:")
            for ssid, signal in networks:
                ssid = ssid.strip()
                signal = int(signal.strip())
                rssi = percentage_to_dbm(signal)
                if rssi is None:
                    continue
                distance = calculate_distance(P0, rssi, N)
                if distance is None:
                    continue
                print(
                    f"SSID: {ssid}, Signal Strength: {signal}%, Estimated Distance: {distance:.2f} meters")
        else:
            print("No WiFi networks found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def discover_and_connect_strongest_network():
    """Discover available WiFi networks and connect to the one with the strongest signal."""
    try:
        networks = all_Networks()
        system = platform.system().lower()
        if networks:
            # Reference RSSI at 1 meter, in dBm (example value, replace with measured reference RSSI)
            P0 = -69
            N = 2  # Path-loss exponent (2 for open areas, 3-4 for indoors)

            print("Available WiFi Networks and Signal Strengths:")
            for ssid, signal in networks:
                ssid = ssid.strip()
                signal = int(signal.strip())
                rssi = percentage_to_dbm(signal)
                if rssi is None:
                    continue
                distance = calculate_distance(P0, rssi, N)
                if distance is None:
                    continue
                print(
                    f"SSID: {ssid}, Signal Strength: {signal}%, Estimated Distance: {distance:.2f} meters")
            strongest_network = max(networks, key=lambda x: int(x[1]))

            ssid_to_connect = strongest_network[0].strip()
            signal_strength = strongest_network[1]
            print(
                f"Attempting to connect to the strongest network: {ssid_to_connect} with Signal Strength: {signal_strength}%")
            if system == "windows":
                connect_command = f"netsh wlan connect name=\"{ssid_to_connect}\""
            elif system == "linux":
                connect_command = f"nmcli dev wifi connect \"{ssid_to_connect}\""
            elif system == "darwin":
                connect_command = f"networksetup -setairportnetwork en0 \"{ssid_to_connect}\""
            subprocess.call(connect_command, shell=True)

            print(f"Connecting to {ssid_to_connect}...")
        else:
            print("No WiFi networks found.")
    except Exception as e:
        print(f"An error occurred: {e}")


def plot_all_wifi_signal_strengths_over_time():
    """Plot the WiFi signal strengths of all available networks over time."""
    try:
        plt.ion()  # Interactive mode for real-time plotting
        fig, ax = plt.subplots()
        # Set Y-axis limits (signal strength in percentage)
        ax.set_ylim(0, 100)
        ax.set_title("WiFi Signal Strengths of All Networks Over Time")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Signal Strength (%)")

        times = []  # List to store time values
        all_signals = {}  # Dictionary to store signal strengths for each SSID

        start_time = time.time()  # Start time for the plot

        while True:
            networks = all_Networks()
            if networks:
                elapsed_time = time.time() - start_time  # Calculate elapsed time
                times.append(elapsed_time)

                # Store signal strengths for each SSID over time
                for ssid, signal in networks:
                    signal_strength = int(signal.strip())  # Convert to integer
                    if ssid not in all_signals:
                        all_signals[ssid] = []
                    all_signals[ssid].append(signal_strength)

                # Clear and update plot
                ax.clear()
                ax.set_ylim(0, 100)  # Set Y-axis limits
                for ssid, signal_strengths in all_signals.items():
                    ax.plot(times, signal_strengths, label=ssid)
                ax.set_title("WiFi Signal Strengths of All Networks Over Time")
                ax.set_xlabel("Time (s)")
                ax.set_ylabel("Signal Strength (%)")
                ax.legend()
                plt.draw()
                plt.pause(1)
            else:
                print("No WiFi networks found.")
            time.sleep(0.001)  # Small delay to prevent high CPU usage
    except KeyboardInterrupt:
        print("Plotting stopped.")
        plt.ioff()  # Turn off interactive mode
        plt.show()
    except Exception as e:
        print(f"An error occurred: {e}")


def check_internet_connectivity(timeout=5):
    """Check if internet connection is available"""
    try:
        # Try to connect to Google's DNS
        socket.create_connection(("8.8.8.8", 53), timeout)
        return True
    except OSError:
        pass
    
    # Try alternative method with HTTP request
    try:
        response = requests.get('http://www.google.com', timeout=timeout)
        return response.status_code == 200
    except:
        return False


def detect_cellular_network():
    """
    Detect cellular network type (4G/3G/2G)
    This is a basic implementation - in practice you'd use specific APIs
    """
    system = platform.system().lower()
    
    try:
        if system == "windows":
            # Check for mobile broadband adapters
            p = subprocess.Popen(
                ["netsh", "mbn", "show", "interfaces"],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            out, _ = p.communicate()
            output = out.decode('utf-8', errors='ignore')
            
            if "Connected" in output:
                # This is simplified - real implementation would parse signal strength
                return "4G"  # Assume 4G if mobile broadband is connected
                
        elif system == "linux":
            # Check for mobile data interfaces
            p = subprocess.Popen(
                ["nmcli", "dev", "status"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            out, _ = p.communicate()
            output = out.decode('utf-8', errors='ignore')
            
            if "gsm" in output.lower() or "lte" in output.lower():
                return "4G"
            elif "3g" in output.lower() or "umts" in output.lower():
                return "3G"
            elif "2g" in output.lower() or "edge" in output.lower():
                return "2G"
                
    except Exception as e:
        print(f"Error detecting cellular network: {e}")
    
    return None


def estimate_bandwidth():
    """
    Estimate current bandwidth using speed test
    Simplified implementation - returns rough estimate
    """
    try:
        # Quick connectivity test
        start_time = time.time()
        response = requests.get('http://www.google.com', timeout=10)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Very rough bandwidth estimation based on response time
        if response_time < 0.5:
            return 10000  # ~10 Mbps
        elif response_time < 1.0:
            return 5000   # ~5 Mbps
        elif response_time < 2.0:
            return 2000   # ~2 Mbps
        else:
            return 500    # ~0.5 Mbps
            
    except Exception as e:
        print(f"Bandwidth estimation failed: {e}")
        return 0


def get_comprehensive_network_status():
    """Get complete network status including WiFi, cellular, and connectivity"""
    status = {
        'wifi': None,
        'cellular': None,
        'internet': False,
        'bandwidth_estimate': 0,
        'primary_connection': 'offline'
    }
    
    try:
        # Check WiFi
        wifi_data = read_data_from_cmd()
        if wifi_data:
            strongest_signal = max(int(signal) for _, signal in wifi_data)
            status['wifi'] = {
                'connected': True,
                'signal_strength': strongest_signal,
                'networks': wifi_data
            }
            status['primary_connection'] = 'wifi'
        
        # Check cellular
        cellular_type = detect_cellular_network()
        if cellular_type:
            status['cellular'] = {
                'connected': True,
                'type': cellular_type
            }
            if status['primary_connection'] == 'offline':
                status['primary_connection'] = 'cellular'
        
        # Check internet connectivity
        status['internet'] = check_internet_connectivity()
        
        # Estimate bandwidth if we have connectivity
        if status['internet']:
            status['bandwidth_estimate'] = estimate_bandwidth()
            
    except Exception as e:
        print(f"Error getting network status: {e}")
    
    return status


def main():
    """Main function to run the program."""
    print("Choose an option:")
    print("1: Display Signal Strength and Distance of the Access Point you're Connecting to")
    print("2: View Signal Strength of the Access Point you're Connecting to Over Time")
    print("3: Discover Active WiFi Networks")
    print("4: Connect to the Strongest WiFi Network ")
    print("5: Display All WiFi Signals")
    print("6: Check Internet Connectivity")
    print("7: Detect Cellular Network")
    print("8: Get Comprehensive Network Status")

    choice = input("Enter 1-8: ").strip()

    if choice == "1":
        print("Displaying WiFi Signal Strength...")
        display_signal_strength()
    elif choice == "2":
        print("Plotting WiFi Signal Strength Over Time...")
        plot_signal_strength_over_time()
    elif choice == "3":
        print("Discovering Active WiFi Networks...")
        discover_wifi_networks()
    elif choice == "4":
        print("Connecting to the Strongest WiFi Network...")
        discover_and_connect_strongest_network()
    elif choice == "5":
        print("Displaying Signal Strengths of All WiFi Networks Over Time...")
        plot_all_wifi_signal_strengths_over_time()
    elif choice == "6":
        print("Checking Internet Connectivity...")
        connected = check_internet_connectivity()
        print(f"Internet connection: {'Available' if connected else 'Not available'}")
    elif choice == "7":
        print("Detecting Cellular Network...")
        cellular = detect_cellular_network()
        print(f"Cellular network: {cellular if cellular else 'Not detected'}")
    elif choice == "8":
        print("Getting Comprehensive Network Status...")
        status = get_comprehensive_network_status()
        print(f"Network Status: {status}")
    else:
        print("Invalid choice. Please run the program again and select a valid option.")


if __name__ == "__main__":
    main()
