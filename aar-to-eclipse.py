#!/usr/bin/env python3
#
# Copyright 2015 HiHex Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

import argparse
import pathlib
import zipfile
import subprocess
import shutil
import sys
import uuid
import xml.etree.ElementTree as xml


BUILD_XML = '''\
<?xml version="1.0" encoding="UTF-8"?>
<project name="." default="help">
    <property file="local.properties"/>
    <property file="ant.properties"/>
    <property environment="env"/>
    <condition property="sdk.dir" value="${env.ANDROID_HOME}">
        <isset property="env.ANDROID_HOME"/>
    </condition>
    <loadproperties srcFile="project.properties"/>
    <fail
        message="sdk.dir is missing. Make sure to generate local.properties using 'android update lib-project' or to inject it through the ANDROID_HOME environment variable."
        unless="sdk.dir"
    />
    <import file="custom_rules.xml" optional="true"/>
    <!-- version-tag: 1 -->
    <import file="${sdk.dir}/tools/ant/build.xml"/>
</project>
'''

PROJECT_PROPERTIES_TEMPLATE = '''\
proguard.config=${{sdk.dir}}/tools/proguard/proguard-android.txt:proguard.txt
android.library=true
target=android-{}
'''




def create_arg_parser():
    parser = argparse.ArgumentParser(description='''
            Convert *.aar to Eclipse library project
    ''')
    parser.add_argument('-o', '--output', help='''
            the directory to contain the Eclipse library project; by default it
            will write to a directory having the same name as the *.aar file
    ''')
    parser.add_argument('-f', '--force', action='store_true', help='''
            force rewriting the output directory even if it already exists
    ''')
    parser.add_argument('aar', help='''
            the input *.aar file
    ''')
    return parser




def merge_libs(output_dir):
    '''Move all libraries back into the libs/ directory.'''

    libs_dir = output_dir / 'libs'
    try:
        libs_dir.mkdir()
    except FileExistsError:
        pass

    try:
        jni_dir = output_dir / 'jni'
        for child in jni_dir.iterdir():
            target_path = libs_dir / child.relative_to(jni_dir)
            child.rename(target_path)
        jni_dir.rmdir()
    except FileNotFoundError:
        pass

    target_path = libs_dir / 'classes.jar'
    source_path = output_dir / 'classes.jar'
    while True:
        if target_path.exists():
            target_path = libs_dir / 'classes.{}.jar'.format(uuid.uuid4())
        else:
            source_path.rename(target_path)
            break


def write_eclipse_specific_files(output_dir):
    # proguard.txt (required even if we don't run proguard)
    (output_dir / 'proguard.txt').touch()

    # project.properties
    tree = xml.parse(str(output_dir / 'AndroidManifest.xml'))
    target_sdk = tree.find('uses-sdk').get('{http://schemas.android.com/apk/res/android}targetSdkVersion')

    with (output_dir / 'project.properties').open('w') as f:
        f.write(PROJECT_PROPERTIES_TEMPLATE.format(target_sdk))

    # build.xml
    with (output_dir / 'build.xml').open('w') as f:
        f.write(BUILD_XML)

    (output_dir / 'src').touch()




def convert(aar, output_dir):
    aar.extractall(str(output_dir))
    merge_libs(output_dir)
    write_eclipse_specific_files(output_dir)
    try:
        (output_dir / 'aapt/AndroidManifest.xml').unlink()
    except FileNotFoundError:
        pass
    try:
        subprocess.call(['android', 'update', 'lib-project', '-p', str(output_dir)])
    except FileNotFoundError:
        print('Warning: Cannot create "local.properties".',
              'Please perform `android update lib-project` manually.', file=sys.stderr)



def main():
    parser = create_arg_parser()

    ns = parser.parse_args()
    if ns.output is not None:
        output_dir = pathlib.Path(ns.output)
    else:
        output_dir = pathlib.Path(ns.aar).with_suffix('')

    try:
        output_dir.mkdir()
    except FileExistsError:
        try:
            output_dir.rmdir()
        except OSError:
            if ns.force:
                shutil.rmtree(str(output_dir))
            else:
                print('Output folder "{}" already exists.'.format(output_dir),
                      'Please remove it or choose another name.', file=sys.stderr)
                return 1

    with zipfile.ZipFile(ns.aar) as aar:
        convert(aar, output_dir)

    print('Done.', file=sys.stderr)

    return 0



if __name__ == '__main__':
    sys.exit(main())

