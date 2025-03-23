import random
import string
import subprocess
import os
import time
import multiprocessing
from multiprocessing import Pool, Manager
import argparse
import math
import uuid

# C program template with common headers
C_TEMPLATE = '''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <time.h>
#include <assert.h>
#include <errno.h>
#include <float.h>
#include <limits.h>
#include <locale.h>
#include <setjmp.h>
#include <signal.h>
#include <stdarg.h>
#include <stddef.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <pthread.h>
#include <dirent.h>
#include <termios.h>

int main(int argc, char **argv) {
%s
    return 0;
}
'''

def calculate_combinations(charset_size, length):
    """Calculate the number of possible combinations"""
    return charset_size ** length

def format_large_number(number):
    """Format large numbers for readability"""
    if number < 1e6:
        return f"{number:,}"
    
    exponent = math.floor(math.log10(number))
    mantissa = number / 10**exponent
    
    return f"{mantissa:.2f} × 10^{exponent}"

def get_charset(include_lowercase=True, include_uppercase=True, include_digits=True, 
                include_symbols=True, include_whitespace=False, custom_charset=None):
    """Get character set based on specified options"""
    if custom_charset:
        return custom_charset
        
    charset = ""
    if include_lowercase:
        charset += string.ascii_lowercase
    if include_uppercase:
        charset += string.ascii_uppercase
    if include_digits:
        charset += string.digits
    if include_symbols:
        charset += "+-*/=<>!&|^%~?:;,.(){}[]\'\"\\"
    if include_whitespace:
        charset += " \t\n"
    return charset

def generate_random_c_content(size, charset):
    """Generate random C code content of specified size"""
    return ''.join(random.choice(charset) for _ in range(size))

def test_compilation(content, pid, compiler, timeout=2):
    """Test if the generated content compiles"""
    unique_id = uuid.uuid4().hex[:8]
    filename = f"{pid}_{unique_id}"
    c_file = f"{filename}.c"
    
    # Write to file
    with open(c_file, "w") as f:
        f.write(C_TEMPLATE % content)
    
    # Try to compile
    try:
        result = subprocess.run([compiler, "-c", c_file], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            timeout=timeout,
                            text=True)
        success = result.returncode == 0
        error_message = result.stderr if not success else ""
        
        # If compilation failed, remove the file
        if not success:
            os.remove(c_file)
            if os.path.exists(f"{filename}.o"):
                os.remove(f"{filename}.o")
    except Exception as e:
        success = False
        error_message = str(e)
        if os.path.exists(c_file):
            os.remove(c_file)
    
    # Remove object file if it exists
    if os.path.exists(f"{filename}.o"):
        os.remove(f"{filename}.o")
    
    return success, content, c_file if success else None, error_message

def worker(args):
    """Worker process function"""
    task_id, counter_lock, successful_count, total_count, byte_size, charset, compiler, show_errors = args
    pid = os.getpid()
    
    # Set different random seed for each process
    random.seed(pid + task_id)
    
    content = generate_random_c_content(byte_size, charset)
    success, content, filename, error_message = test_compilation(content, pid, compiler)
    
    with counter_lock:
        total_count.value += 1
        if success:
            successful_count.value += 1
            print(f"Compilation successful! ({successful_count.value}/{total_count.value}) - Saved as {filename}")
        elif show_errors:
            # Print truncated error message if requested
            print(f"Compilation failed: {error_message[:100]}..." if len(error_message) > 100 else f"Compilation failed: {error_message}")
        
        # Periodically print statistics
        if total_count.value % 100 == 0:
            success_rate = successful_count.value / total_count.value * 100
            print(f"Progress: {total_count.value} attempts, {successful_count.value} successes ({success_rate:.2f}%)")
    
    return success

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Random C Code Compiler Tester')
    parser.add_argument('byte_size', type=int, nargs='?', default=5, 
                        help='Byte size of C code to test (default: 5)')
    parser.add_argument('--tasks', type=int, default=10000, 
                        help='Number of tasks to test (default: 10000, -1: unlimited)')
    parser.add_argument('--no-lowercase', action='store_true', help='Exclude lowercase letters')
    parser.add_argument('--no-uppercase', action='store_true', help='Exclude uppercase letters')
    parser.add_argument('--no-digits', action='store_true', help='Exclude digits')
    parser.add_argument('--no-symbols', action='store_true', help='Exclude symbols')
    parser.add_argument('--whitespace', action='store_true', help='Include whitespace characters')
    parser.add_argument('--charset', type=str, help='Custom character set to use (overrides other charset options)')
    parser.add_argument('--compiler', type=str, default='gcc', help='Compiler to use (default: gcc)')
    parser.add_argument('--show-errors', action='store_true', help='Show compilation error messages')
    parser.add_argument('--timeout', type=int, default=2, help='Compilation timeout in seconds (default: 2)')
    args = parser.parse_args()
    
    # Get character set based on arguments
    charset = get_charset(
        include_lowercase=not args.no_lowercase,
        include_uppercase=not args.no_uppercase,
        include_digits=not args.no_digits,
        include_symbols=not args.no_symbols,
        include_whitespace=args.whitespace,
        custom_charset=args.charset
    )
    
    if not charset:
        print("Error: At least one character type must be included")
        return
    
    # Calculate combinations
    charset_size = len(charset)
    combinations = calculate_combinations(charset_size, args.byte_size)
    
    print(f"Starting random C code compilation test with {args.byte_size} bytes")
    print(f"Character set size: {charset_size} characters")
    print(f"Character set: {charset[:50]}{'...' if len(charset) > 50 else ''}")
    print(f"Compiler: {args.compiler}")
    print(f"Total possible combinations: {format_large_number(combinations)}")
    
    # Multiprocessing setup
    cpu_count = multiprocessing.cpu_count()
    print(f"Available CPU cores: {cpu_count}")
    
    # Shared variables
    manager = Manager()
    counter_lock = manager.Lock()
    successful_count = manager.Value('i', 0)
    total_count = manager.Value('i', 0)
    
    start_time = time.time()
    
    # Create output directory if it doesn't exist
    os.makedirs("successful_codes", exist_ok=True)
    
    # Handle unlimited mode
    if args.tasks == -1:
        print("Running in unlimited task mode... (Press Ctrl+C to stop)")
        
        task_id = 0
        
        try:
            with Pool(processes=cpu_count) as pool:
                while True:
                    # Create batch of tasks
                    batch_size = cpu_count * 10
                    tasks = [(task_id + i, counter_lock, successful_count, total_count, 
                             args.byte_size, charset, args.compiler, args.show_errors) 
                            for i in range(batch_size)]
                    task_id += batch_size
                    
                    # Execute tasks asynchronously
                    results = pool.map(worker, tasks)
                    
                    # Print progress
                    elapsed = time.time() - start_time
                    rate = total_count.value / elapsed if elapsed > 0 else 0
                    print(f"Processing speed: {rate:.2f} per second (total: {total_count.value})")
        
        except KeyboardInterrupt:
            print("\nStopped by user")
    
    else:
        # Fixed number of tasks
        tasks = [(i, counter_lock, successful_count, total_count, args.byte_size, 
                 charset, args.compiler, args.show_errors) 
                for i in range(args.tasks)]
        
        try:
            with Pool(processes=cpu_count) as pool:
                for _ in pool.imap_unordered(worker, tasks):
                    pass
        
        except KeyboardInterrupt:
            print("\nStopped by user")
    
    # Print results
    try:
        elapsed = time.time() - start_time
        rate = total_count.value / elapsed if elapsed > 0 else 0
        success_rate = successful_count.value / total_count.value * 100 if total_count.value > 0 else 0
        
        print(f"\nTask completed. Total: {total_count.value} attempts, {successful_count.value} successes ({success_rate:.2f}%)")
        print(f"Processing speed: {rate:.2f} per second")
        print(f"Time elapsed: {elapsed:.2f} seconds")
        
        # Estimate time needed for all combinations
        if rate > 0:
            seconds_needed = combinations / rate
            if seconds_needed < 60:
                time_estimate = f"{seconds_needed:.2f} seconds"
            elif seconds_needed < 3600:
                time_estimate = f"{seconds_needed/60:.2f} minutes"
            elif seconds_needed < 86400:
                time_estimate = f"{seconds_needed/3600:.2f} hours"
            elif seconds_needed < 31536000:
                time_estimate = f"{seconds_needed/86400:.2f} days"
            elif seconds_needed < 31536000*100:
                time_estimate = f"{seconds_needed/31536000:.2f} years"
            else:
                time_estimate = f"{format_large_number(seconds_needed/31536000)} years"
            
            print(f"Testing all combinations would take approximately {time_estimate}")
    
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
