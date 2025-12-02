For this project, I took the existing MLForensics code and added all the required software quality assurance pieces: fuzzing, forensic logging, and continuous integration. I wrote a fuzz.py script that automatically tests five functions from the project (getAllSLOC, Average, Median, makeChunks, and dumpContentIntoFile) using randomly generated inputs. It creates temporary files, random lists, and random strings, and runs 50 rounds per execution. The results go into a fuzz\_results.txt file, and none of the functions crashed during any run.



I also added logging to those same five functions by using Python’s logging module. Each function now logs what it’s doing—things like input sizes, file paths, calculated values, and any exceptions. Running the fuzzer makes the logs show up in the console, which helped confirm that the instrumentation was actually being hit.



To tie everything together, I set up a GitHub Actions workflow (ci.yml) that installs Python, installs the needed packages, and runs python fuzz.py every time I push to the main branch. At first the workflow failed because I hadn’t pushed all my changes, but once everything was committed, the CI runs turned green. Now the project automatically fuzzes itself in a clean environment on every push.



Overall, this project showed me how useful it is to combine fuzzing, logging, and CI. It gives quick feedback if something breaks, and it makes even a small project feel much more reliable and easier to maintain.

