#!/bin/bash
# JDK 21 Environment Setup
export JAVA_HOME="./artifacts/jdk21/jdk-21.0.8+9/Contents/Home"
export PATH="$JAVA_HOME/bin:$PATH"
echo "JDK 21 environment activated"
java -version
