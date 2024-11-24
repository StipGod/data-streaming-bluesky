package com.example;

import ai.djl.Application;
import ai.djl.ModelException;
import ai.djl.inference.Predictor;
import ai.djl.modality.Classifications;
import ai.djl.repository.zoo.Criteria;
import ai.djl.repository.zoo.ZooModel;
import ai.djl.training.util.ProgressBar;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.apache.flink.api.common.functions.MapFunction;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.common.serialization.SerializationSchema;
import org.apache.flink.connector.kinesis.sink.KinesisStreamsSink;
import org.apache.flink.connector.kinesis.source.KinesisStreamsSource;
import org.apache.flink.connector.kinesis.source.KinesisStreamsSourceBuilder;
import org.apache.flink.configuration.Configuration;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;

import java.io.IOException;
import java.time.Duration;
import java.util.Properties;

public class SentimentAnalysis {

    public static void main(String[] args) throws Exception {
        // Initialize the Flink execution environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();

        // Input Kinesis Stream configuration
        Configuration inputConfig = new Configuration();
        inputConfig.setString("aws.region", "us-east-1");




        KinesisStreamsSource<String> kinesisSource = KinesisStreamsSource.<String>builder()
                .setStreamArn("arn:aws:kinesis:us-east-1:700361004035:stream/Bluesky") // Replace with your input stream ARN
                .setDeserializationSchema(new SimpleStringSchema())
                .setSourceConfig(inputConfig)
                .build();

        // Output Kinesis Stream configuration
        Properties outputProperties = new Properties();
        outputProperties.setProperty("aws.region", "us-east-1");

        KinesisStreamsSink<String> kinesisSink = KinesisStreamsSink.<String>builder()
                .setStreamArn("arn:aws:kinesis:us-east-1:700361004035:stream/flink-dynamodb") // Replace with your output stream ARN
                .setSerializationSchema(new SimpleStringSchema())
                .setPartitionKeyGenerator(element -> String.valueOf(element.hashCode()))
                .setKinesisClientProperties(outputProperties) 
                .build();

        // Read data from the Kinesis source
        DataStream<String> kinesisInput = env.fromSource(
        kinesisSource,
        WatermarkStrategy.<String>forMonotonousTimestamps().withIdleness(Duration.ofSeconds(1)),
        "Kinesis Source")
        .returns(org.apache.flink.api.common.typeinfo.Types.STRING); // Explicitly set the return type
        // Apply sentiment analysis
        DataStream<String> sentimentResults = kinesisInput
                .map(new SentimentAnalysisFunction())
                .name("Sentiment Analysis");

        // Write data to the Kinesis sink
        sentimentResults.sinkTo(kinesisSink).name("Kinesis Sink");

        // Execute the Flink job
        env.execute("Sentiment Analysis Pipeline");
    }

    // MapFunction for sentiment analysis
    public static class SentimentAnalysisFunction implements MapFunction<String, String> {
        private static final ObjectMapper objectMapper = new ObjectMapper();
        private static Predictor<String, Classifications> predictor;

        private Predictor<String, Classifications> getOrCreatePredictor() throws ModelException, IOException {
            if (predictor == null) {
                Criteria<String, Classifications> criteria = Criteria.builder()
                        .optApplication(Application.NLP.SENTIMENT_ANALYSIS)
                        .setTypes(String.class, Classifications.class)
                        .optProgress(new ProgressBar())
                        .build();
                ZooModel<String, Classifications> model = criteria.loadModel();
                predictor = model.newPredictor();
            }
            return predictor;
        }

        @Override
        public String map(String value) throws Exception {
            Predictor<String, Classifications> predictor = getOrCreatePredictor();

            // Parse the input JSON
            InputRecord inputRecord = objectMapper.readValue(value, InputRecord.class);

            // Perform sentiment analysis on the content field
            Classifications result = predictor.predict(inputRecord.getContent());

            // Construct the output JSON
            OutputRecord outputRecord = new OutputRecord(
                    inputRecord.getAuthor(),
                    inputRecord.getContent(),
                    inputRecord.getcreated_at(),
                    result.best().getClassName()
            );

            return objectMapper.writeValueAsString(outputRecord);
        }
    }

    // Input JSON structure
    public static class InputRecord {
        private String author;
        private String content;
        private String created_at;

        // Getters and setters
        public String getAuthor() { return author; }
        public void setAuthor(String author) { this.author = author; }

        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }

        public String getcreated_at() { return created_at; }
        public void setcreated_at(String created_at) { this.created_at = created_at; }
    }

    // Output JSON structure
    public static class OutputRecord {
        private String author;
        private String content;
        private String created_at;
        private String sentiment;

        public OutputRecord(String author, String content, String created_at, String sentiment) {
            this.author = author;
            this.content = content;
            this.created_at = created_at;
            this.sentiment = sentiment;
        }

        // Getters and setters
        public String getAuthor() { return author; }
        public void setAuthor(String author) { this.author = author; }

        public String getContent() { return content; }
        public void setContent(String content) { this.content = content; }

        public String getcreated_at() { return created_at; }
        public void setcreated_at(String created_at) { this.created_at = created_at; }

        public String getSentiment() { return sentiment; }
        public void setSentiment(String sentiment) { this.sentiment = sentiment; }
    }
}
