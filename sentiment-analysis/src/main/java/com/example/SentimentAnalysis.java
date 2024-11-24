/*
 * Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file except in compliance
 * with the License. A copy of the License is located at
 *
 * http://aws.amazon.com/apache2.0/
 *
 * or in the "license" file accompanying this file. This file is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
 * OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions
 * and limitations under the License.
 */
package com.example;

import java.time.Duration;

import ai.djl.Application;
import ai.djl.ModelException;
import ai.djl.inference.Predictor;
import ai.djl.modality.Classifications;
import ai.djl.repository.zoo.Criteria;
import ai.djl.repository.zoo.ZooModel;
import ai.djl.training.util.ProgressBar;

import org.apache.flink.api.common.functions.FlatMapFunction;
import org.apache.flink.api.java.utils.ParameterTool;
import org.apache.flink.streaming.api.datastream.DataStream;
import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.util.Collector;

import org.apache.flink.streaming.api.environment.StreamExecutionEnvironment;
import org.apache.flink.connector.kinesis.source.KinesisStreamsSource;
import org.apache.flink.connector.kinesis.sink.KinesisStreamsSink;
import org.apache.flink.api.common.serialization.SimpleStringSchema;
import org.apache.flink.api.common.typeinfo.TypeInformation;
import org.apache.flink.api.common.eventtime.WatermarkStrategy;
import com.amazonaws.services.kinesisanalytics.runtime.KinesisAnalyticsRuntime;
import org.apache.flink.streaming.api.environment.LocalStreamEnvironment;

import java.io.IOException;
import java.util.Properties;
import java.util.Map;

/**
 * Implements a streaming version of the sentiment analysis program.
 *
 * <p>This program connects to a server socket and reads strings from the socket. The easiest way to
 * try this out is to open a text server (at port 12345) using the <i>netcat</i> tool via
 *
 * <pre>
 * nc -l 12345 on Linux or nc -l -p 12345 on Windows
 * </pre>
 *
 * <p>and run this example with the hostname and the port as arguments.
 */
public class SentimentAnalysis {
    private static boolean isLocal(StreamExecutionEnvironment env) {
        return env instanceof LocalStreamEnvironment;
    }

    private static final String LOCAL_APPLICATION_PROPERTIES_RESOURCE = "resources/flink-application-properties-dev.json";
    private static Map<String, Properties> loadApplicationProperties(StreamExecutionEnvironment env) throws IOException {
        if (isLocal(env)) {
            return KinesisAnalyticsRuntime.getApplicationProperties(
                    SentimentAnalysis.class.getClassLoader()
                            .getResource(LOCAL_APPLICATION_PROPERTIES_RESOURCE).getPath());
        } else {
            return KinesisAnalyticsRuntime.getApplicationProperties();
        }
    }

    public static void main(String[] args) throws Exception {
        // the host and the port to connect to

        // get the execution environment
        StreamExecutionEnvironment env = StreamExecutionEnvironment.getExecutionEnvironment();
        KinesisStreamsSource<String> kdsSource =
                KinesisStreamsSource.<String>builder()
                        .setStreamArn("arn:aws:kinesis:us-east-1:700361004035:stream/Bluesky")
                        .setDeserializationSchema(new SimpleStringSchema())
                        .build();

      //  final Map<String, Properties> applicationProperties = loadApplicationProperties(env);
        //Properties properties = applicationProperties.get("OutputStream0");

        Properties outputProperties = new Properties();
        outputProperties.setProperty("aws.region", "us-east-1");
        outputProperties.setProperty("aws.arn", "arn:aws:kinesis:us-east-1:700361004035:stream/flink-dynamodb");


        KinesisStreamsSink<String> kdsSink =
        KinesisStreamsSink.<String>builder()
                .setStreamArn("arn:aws:kinesis:us-east-1:700361004035:stream/flink-dynamodb")
                .setKinesisClientProperties(
                        outputProperties
            )
                .setSerializationSchema(new SimpleStringSchema())
                .setPartitionKeyGenerator(element -> String.valueOf(element.hashCode()))
                .build();

        DataStream<String> kinesisRecordsWithEventTimeWatermarks = env.fromSource(kdsSource, WatermarkStrategy.<String>forMonotonousTimestamps().withIdleness(Duration.ofSeconds(1)), "Kinesis source")
                .returns(TypeInformation.of(String.class))
                .uid("custom-uid");

        kinesisRecordsWithEventTimeWatermarks.sinkTo(kdsSink);




        // Run inference with Flink streaming
        //DataStream<Classifications> classifications = kinesisStream.flatMap(new SAFlatMap());

        // print the results with a single thread, rather than in parallel
        // classifications.print().setParallelism(1);
        env.execute("SentimentAnalysis");
    }
    public static class SAFlatMap implements FlatMapFunction<String, Classifications> {

        private static Predictor<String, Classifications> predictor;

        private Predictor<String, Classifications> getOrCreatePredictor()
                throws ModelException, IOException {
            if (predictor == null) {
                Criteria<String, Classifications> criteria =
                        Criteria.builder()
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
        public void flatMap(String value, Collector<Classifications> out) throws Exception {
            Predictor<String, Classifications> predictor = getOrCreatePredictor();
            Classifications classifications = predictor.predict(value);
            out.collect(classifications);
        }
    }

}
