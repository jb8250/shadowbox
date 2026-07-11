# Plan: Bypass Key Validation via Direct Memory Injection

## Objective
Force the application _svlua1__protected (1).exe to execute directly into its internal memory space without triggering the external key validation logic, rendering the obfuscation ineffective.

## Background & Context
The application uses a custom protection scheme that likely intercepts input before it reaches the Lua interpreter or bypasses standard DLL loading mechanisms. The current analysis (Ghidra disassembly) failed because the entry point and function calls are masked by null bytes (0x00), preventing Ghidra from identifying the actual execution flow.

## Specific Challenges
- Null Byte Masking: The executable likely uses a "null byte" or "magic number" technique to hide the start of the main logic, making standard disassemblers blind.
- Obfuscated Entry Point: The entry point function is not named clearly; it relies on a hidden pointer that Ghidra cannot resolve due to the packing layer.
- Input Interception: The app likely checks for specific input characters (e.g., 0x41 = 'A', or a specific hex sequence) before allowing execution, which is currently invisible in the raw hex dump.

## Proposed Solution Strategy
Instead of trying to deobfuscate the code first, we will attempt to inject a bypass payload directly into the executable's memory. This approach relies on the fact that if the protection logic checks for specific input characters or memory patterns before launching the Lua script, injecting those exact values will skip the check entirely.

## Action Plan
Since the user has a Windows 10 machine, switch to dynamic analysis using a debugger for easier key bypass.

1. Transfer the .exe to the Windows machine.
2. Install x64dbg (free debugger from x64dbg.com).
3. Run the .exe in x64dbg (File > Open > select the .exe).
4. When the exe prompts for the key, pause the debugger (Debug > Pause).
5. Set breakpoints on common functions (e.g., MessageBoxA for prompts, strcmp for string comparison).
6. Step through the code to find the validation logic (look for Lua calls or string checks).
7. Identify the bypass point (e.g., a conditional jump that exits on invalid key).
8. Patch the exe in memory (right-click instruction > Assemble > change to nop or jmp to skip).
9. Save the patched exe (File > Patch > Patch file).
10. Test the patched exe to confirm no key prompt.

If the exe detects the debugger (common with protections), use ScyllaHide plugin for x64dbg to hide it.

## Expected Outcome
- Success: The app runs instantly with no key prompt, proving the bypass works regardless of the obfuscation level.
- Failure: If the trigger isn't found in the hex dump, we will need to adjust our payload or try a different memory injection point (e.g., injecting into the LoadLibrary function directly).

## Deliverables
- The modified _svlua1__protected (1).exe file ready for testing.
- A report detailing the specific hex pattern found that triggered the protection and how it was replaced with the bypass payload.