plugins {
    java
    application
}
apply(file("gradle/javaFormatter.gradle.kts"))

group = "com.example"
version = "1.0-SNAPSHOT"

repositories {
    mavenCentral()
    maven("https://oss.sonatype.org/content/repositories/snapshots/")
}

dependencies {
    implementation(platform("ai.djl:bom:${property("djl_version")}"))
    implementation("ai.djl:api")
    implementation("org.apache.flink:flink-streaming-java:${property("flint_version")}")
    implementation("org.apache.flink:flink-connector-kinesis:${property("flink_kinesis_connector")}")
    implementation("org.apache.flink:flink-connector-base:1.20.0")
    implementation("com.amazonaws:aws-java-sdk-kinesis:${property("awsSdkVersion")}")
    implementation("com.amazonaws:aws-kinesisanalytics-runtime:1.2.0") // AWS Kinesis Analytics SDK

    runtimeOnly("org.apache.flink:flink-clients:${property("flint_version")}")
    runtimeOnly("ai.djl.pytorch:pytorch-model-zoo")
    runtimeOnly("org.slf4j:slf4j-simple:${property("slf4j_version")}")
}

tasks {
    application {
        mainClass = "com.example.SentimentAnalysis"
        applicationDefaultJvmArgs = listOf(
            "--add-opens",
            "java.base/java.lang=ALL-UNNAMED",
            "--add-opens",
            "java.base/java.util=ALL-UNNAMED",
            "-Dorg.slf4j.simpleLogger.log.org.apache.flink=off"
        )
    }
}