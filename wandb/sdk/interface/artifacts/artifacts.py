from typing import TYPE_CHECKING, Dict, List, Optional, Sequence, Union

import wandb
from wandb import hashutil, util
from wandb.data_types import WBValue

if TYPE_CHECKING:
    # need this import for type annotations, but want to avoid circular dependency
    import wandb.apis.public
    from wandb.sdk import wandb_artifacts


class ArtifactManifest:
    entries: Dict[str, "ArtifactEntry"]

    @classmethod
    # TODO: we don't need artifact here.
    def from_manifest_json(cls, artifact, manifest_json) -> "ArtifactManifest":
        if "version" not in manifest_json:
            raise ValueError("Invalid manifest format. Must contain version field.")
        version = manifest_json["version"]
        for sub in cls.__subclasses__():
            if sub.version() == version:
                return sub.from_manifest_json(artifact, manifest_json)
        raise ValueError("Invalid manifest version.")

    @classmethod
    def version(cls):
        pass

    def __init__(
        self,
        artifact,
        storage_policy: "wandb_artifacts.WandbStoragePolicy",
        entries=None,
    ) -> None:
        self.artifact = artifact
        self.storage_policy = storage_policy
        self.entries = entries or {}

    def to_manifest_json(self):
        raise NotImplementedError()

    def digest(self):
        raise NotImplementedError()

    def add_entry(self, entry):
        if (
            entry.path in self.entries
            and entry.digest != self.entries[entry.path].digest
        ):
            raise ValueError("Cannot add the same path twice: %s" % entry.path)
        self.entries[entry.path] = entry

    def get_entry_by_path(self, path: str) -> Optional["ArtifactEntry"]:
        return self.entries.get(path)

    def get_entries_in_directory(self, directory):
        return [
            self.entries[entry_key]
            for entry_key in self.entries
            if entry_key.startswith(
                directory + "/"
            )  # entries use forward slash even for windows
        ]


class ArtifactEntry:
    path: util.LogicalFilePathStr
    ref: Optional[Union[util.FilePathStr, util.URIStr]]
    digest: Union[hashutil.B64MD5, util.URIStr, util.FilePathStr, hashutil.ETag]
    birth_artifact_id: Optional[str]
    size: Optional[int]
    extra: Dict
    local_path: Optional[str]

    def parent_artifact(self) -> "Artifact":
        """
        Get the artifact to which this artifact entry belongs.

        Returns:
            (Artifact): The parent artifact
        """
        raise NotImplementedError

    def download(self, root: Optional[str] = None) -> util.FilePathStr:
        """
        Downloads this artifact entry to the specified root path.

        Arguments:
            root: (str, optional) The root path in which to download this
                artifact entry. Defaults to the artifact's root.

        Returns:
            (str): The path of the downloaded artifact entry.

        """
        raise NotImplementedError

    def ref_target(self) -> str:
        """
        Gets the reference URL that this artifact entry targets.
        Returns:
            (str): The reference URL of this artifact entry.
        Raises:
            ValueError: If this artifact entry was not a reference.
        """
        raise NotImplementedError

    def ref_url(self) -> str:
        """
        Gets a URL to this artifact entry such that it can be referenced
        by another artifact.

        Returns:
            (str): A URL representing this artifact entry.

        Examples:
            Basic usage
            ```
            ref_url = source_artifact.get_path('file.txt').ref_url()
            derived_artifact.add_reference(ref_url)
            ```
        """
        raise NotImplementedError


class Artifact:
    @property
    def id(self) -> Optional[str]:
        """
        Returns:
            (str): The artifact's ID
        """
        raise NotImplementedError

    @property
    def version(self) -> str:
        """
        Returns:
            (str): The version of this artifact. For example, if this
                is the first version of an artifact, its `version` will
                be 'v0'.
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """
        Returns:
            (str): The artifact's name
        """
        raise NotImplementedError

    @property
    def type(self) -> str:
        """
        Returns:
            (str): The artifact's type
        """
        raise NotImplementedError

    @property
    def entity(self) -> str:
        """
        Returns:
            (str): The name of the entity this artifact belongs to.
        """
        raise NotImplementedError

    @property
    def project(self) -> str:
        """
        Returns:
            (str): The name of the project this artifact belongs to.
        """
        raise NotImplementedError

    @property
    def manifest(self) -> ArtifactManifest:
        """
        Returns:
            (ArtifactManifest): The artifact's manifest, listing all of its contents.
                You cannot add more files to an artifact once you've retrieved its
                manifest.
        """
        raise NotImplementedError

    @property
    def digest(self) -> str:
        """
        Returns:
            (str): The artifact's logical digest, a checksum of its contents. If
                an artifact has the same digest as the current `latest` version,
                then `log_artifact` is a no-op.
        """
        raise NotImplementedError

    @property
    def state(self) -> str:
        """
        Returns:
            (str): The state of the artifact, which can be one of "PENDING",
                "COMMITTED", or "DELETED".
        """
        raise NotImplementedError

    @property
    def size(self) -> int:
        """
        Returns:
            (int): The size in bytes of the artifact. Includes any references
                tracked by this artifact.
        """
        raise NotImplementedError

    @property
    def commit_hash(self) -> str:
        """
        Returns:
            (str): The artifact's commit hash which is used in http URLs
        """
        raise NotImplementedError

    @property
    def description(self) -> Optional[str]:
        """
        Returns:
            (str): Free text that offers a description of the artifact. The
                description is markdown rendered in the UI, so this is a good place
                to put links, etc.
        """
        raise NotImplementedError

    @description.setter
    def description(self, desc: Optional[str]) -> None:
        """
        Arguments:
            desc: Free text that offers a description of the artifact. The
                description is markdown rendered in the UI, so this is a good place
                to put links, etc.
        """
        raise NotImplementedError

    @property
    def metadata(self) -> dict:
        """
        Returns:
            (dict): Structured data associated with the artifact,
                for example class distribution of a dataset. This will eventually be queryable
                and plottable in the UI. There is a hard limit of 100 total keys.
        """
        raise NotImplementedError

    @metadata.setter
    def metadata(self, metadata: dict) -> None:
        """
        Arguments:
            metadata: (dict) Structured data associated with the artifact,
                for example class distribution of a dataset. This will eventually be queryable
                and plottable in the UI. There is a hard limit of 100 total keys.
        """
        raise NotImplementedError

    @property
    def aliases(self) -> List[str]:
        """
        Returns:
            (list): A list of the aliases associated with this artifact. The list is
                mutable and calling `save()` will persist all alias changes.
        """
        raise NotImplementedError

    @aliases.setter
    def aliases(self, aliases: List[str]) -> None:
        """
        Arguments:
            aliases: (list) The list of aliases associated with this artifact.
        """
        raise NotImplementedError

    def used_by(self) -> List["wandb.apis.public.Run"]:
        """
        Returns:
            (list): A list of the runs that have used this artifact.
        """
        raise NotImplementedError

    def logged_by(self) -> "wandb.apis.public.Run":
        """
        Returns:
            (Run): The run that first logged this artifact.
        """
        raise NotImplementedError

    def new_file(self, name: str, mode: str = "w", encoding: Optional[str] = None):
        """
        Open a new temporary file that will be automatically added to the artifact.

        Arguments:
            name: (str) The name of the new file being added to the artifact.
            mode: (str, optional) The mode in which to open the new file.
            encoding: (str, optional) The encoding in which to open the new file.

        Examples:
            ```
            artifact = wandb.Artifact('my_data', type='dataset')
            with artifact.new_file('hello.txt') as f:
                f.write('hello!')
            wandb.log_artifact(artifact)
            ```

        Returns:
            (file): A new file object that can be written to. Upon closing,
                the file will be automatically added to the artifact.
        """
        raise NotImplementedError

    def add_file(
        self,
        local_path: str,
        name: Optional[str] = None,
        is_tmp: Optional[bool] = False,
    ):
        """
        Adds a local file to the artifact.

        Arguments:
            local_path: (str) The path to the file being added.
            name: (str, optional) The path within the artifact to use for the file being added. Defaults
                to the basename of the file.
            is_tmp: (bool, optional) If true, then the file is renamed deterministically to avoid collisions.
                (default: False)

        Examples:
            Adding a file without an explicit name:
            ```
            artifact.add_file('path/to/file.txt') # Added as `file.txt'
            ```

            Adding a file with an explicit name:
            ```
            artifact.add_file('path/to/file.txt', name='new/path/file.txt') # Added as 'new/path/file.txt'
            ```

        Raises:
            Exception: if problem

        Returns:
            ArtifactManifestEntry: the added manifest entry

        """
        raise NotImplementedError

    def add_dir(self, local_path: str, name: Optional[str] = None) -> None:
        """
        Adds a local directory to the artifact.

        Arguments:
            local_path: (str) The path to the directory being added.
            name: (str, optional) The path within the artifact to use for the directory being added. Defaults
                to files being added under the root of the artifact.

        Examples:
            Adding a directory without an explicit name:
            ```
            artifact.add_dir('my_dir/') # All files in `my_dir/` are added at the root of the artifact.
            ```

            Adding a directory without an explicit name:
            ```
            artifact.add_dir('my_dir/', name='destination') # All files in `my_dir/` are added under `destination/`.
            ```

        Raises:
            Exception: if problem.

        Returns:
            None
        """
        raise NotImplementedError

    def add_reference(
        self,
        uri: Union[ArtifactEntry, str],
        name: Optional[str] = None,
        checksum: bool = True,
        max_objects: Optional[int] = None,
    ):
        """
        Adds a reference denoted by a URI to the artifact. Unlike adding files or directories,
        references are NOT uploaded to W&B. However, artifact methods such as `download()` can
        be used regardless of whether the artifact contains references or uploaded files.

        By default, W&B offers special
        handling for the following schemes:

        - http(s): The size and digest of the file will be inferred by the `Content-Length` and
            the `ETag` response headers returned by the server.
        - s3: The checksum and size will be pulled from the object metadata. If bucket versioning
            is enabled, then the version ID is also tracked.
        - gs: The checksum and size will be pulled from the object metadata. If bucket versioning
            is enabled, then the version ID is also tracked.
        - file: The checksum and size will be pulled from the file system. This scheme is useful if
            you have an NFS share or other externally mounted volume containing files you wish to track
            but not necessarily upload.

        For any other scheme, the digest is just a hash of the URI and the size is left blank.

        Arguments:
            uri: (str) The URI path of the reference to add. Can be an object returned from
                Artifact.get_path to store a reference to another artifact's entry.
            name: (str) The path within the artifact to place the contents of this reference
            checksum: (bool, optional) Whether or not to checksum the resource(s) located at the
                reference URI. Checksumming is strongly recommended as it enables automatic integrity
                validation, however it can be disabled to speed up artifact creation. (default: True)
            max_objects: (int, optional) The maximum number of objects to consider when adding a
                reference that points to directory or bucket store prefix. For S3 and GCS, this limit
                is 10,000 by default but is uncapped for other URI schemes. (default: None)

        Raises:
            Exception: If problem.

        Returns:
            List[ArtifactManifestEntry]: The added manifest entries.

        Examples:
            Adding an HTTP link:
            ```
            # Adds `file.txt` to the root of the artifact as a reference
            artifact.add_reference('http://myserver.com/file.txt')
            ```

            Adding an S3 prefix without an explicit name:
            ```
            # All objects under `prefix/` will be added at the root of the artifact.
            artifact.add_reference('s3://mybucket/prefix')
            ```

            Adding a GCS prefix with an explicit name:
            ```
            # All objects under `prefix/` will be added under `path/` at the top of the artifact.
            artifact.add_reference('gs://mybucket/prefix', name='path')
            ```
        """
        raise NotImplementedError

    def add(self, obj: WBValue, name: str):
        """Adds wandb.WBValue `obj` to the artifact.

        ```
        obj = artifact.get(name)
        ```

        Arguments:
            obj: (wandb.WBValue) The object to add. Currently support one of
                Bokeh, JoinedTable, PartitionedTable, Table, Classes, ImageMask,
                BoundingBoxes2D, Audio, Image, Video, Html, Object3D
            name: (str) The path within the artifact to add the object.

        Returns:
            ArtifactManifestEntry: the added manifest entry

        Examples:
            Basic usage
            ```
            artifact = wandb.Artifact('my_table', 'dataset')
            table = wandb.Table(columns=["a", "b", "c"], data=[[i, i*2, 2**i]])
            artifact.add(table, "my_table")

            wandb.log_artifact(artifact)
            ```

            Retrieving an object:
            ```
            artifact = wandb.use_artifact('my_table:latest')
            table = artifact.get("my_table")
            ```
        """
        raise NotImplementedError

    def get_path(self, name: str) -> ArtifactEntry:
        """
        Gets the path to the file located at the artifact relative `name`.

        NOTE: This will raise an error unless the artifact has been fetched using
        `use_artifact`, fetched using the API, or `wait()` has been called.

        Arguments:
            name: (str) The artifact relative name to get

        Raises:
            Exception: if problem

        Examples:
            Basic usage
            ```
            # Run logging the artifact
            with wandb.init() as r:
                artifact = wandb.Artifact('my_dataset', type='dataset')
                artifact.add_file('path/to/file.txt')
                wandb.log_artifact(artifact)

            # Run using the artifact
            with wandb.init() as r:
                artifact = r.use_artifact('my_dataset:latest')
                path = artifact.get_path('file.txt')

                # Can now download 'file.txt' directly:
                path.download()
            ```
        """
        raise NotImplementedError

    def get(self, name: str) -> WBValue:
        """
        Gets the WBValue object located at the artifact relative `name`.

        NOTE: This will raise an error unless the artifact has been fetched using
        `use_artifact`, fetched using the API, or `wait()` has been called.

        Arguments:
            name: (str) The artifact relative name to get

        Raises:
            Exception: if problem

        Examples:
            Basic usage
            ```
            # Run logging the artifact
            with wandb.init() as r:
                artifact = wandb.Artifact('my_dataset', type='dataset')
                table = wandb.Table(columns=["a", "b", "c"], data=[[i, i*2, 2**i]])
                artifact.add(table, "my_table")
                wandb.log_artifact(artifact)

            # Run using the artifact
            with wandb.init() as r:
                artifact = r.use_artifact('my_dataset:latest')
                table = r.get('my_table')
            ```
        """
        raise NotImplementedError

    def download(
        self, root: Optional[str] = None, recursive: bool = False
    ) -> util.FilePathStr:
        """
        Downloads the contents of the artifact to the specified root directory.

        NOTE: Any existing files at `root` are left untouched. Explicitly delete
        root before calling `download` if you want the contents of `root` to exactly
        match the artifact.

        Arguments:
            root: (str, optional) The directory in which to download this artifact's files.
            recursive: (bool, optional) If true, then all dependent artifacts are eagerly
                downloaded. Otherwise, the dependent artifacts are downloaded as needed.

        Returns:
            (str): The path to the downloaded contents.
        """
        raise NotImplementedError

    def checkout(self, root: Optional[str] = None) -> str:
        """
        Replaces the specified root directory with the contents of the artifact.

        WARNING: This will DELETE all files in `root` that are not included in the
        artifact.

        Arguments:
            root: (str, optional) The directory to replace with this artifact's files.

        Returns:
           (str): The path to the checked out contents.
        """
        raise NotImplementedError

    def verify(self, root: Optional[str] = None) -> bool:
        """
        Verify that the actual contents of an artifact at a specified directory
        `root` match the expected contents of the artifact according to its
        manifest.

        All files in the directory are checksummed and the checksums are then
        cross-referenced against the artifact's manifest.

        NOTE: References are not verified.

        Arguments:
            root: (str, optional) The directory to verify. If None
                artifact will be downloaded to './artifacts/<self.name>/'

        Raises:
            (ValueError): If the verification fails.
        """
        raise NotImplementedError

    def save(self) -> None:
        """
        Persists any changes made to the artifact.

        Returns:
            None
        """
        raise NotImplementedError

    def link(self, target_path: str, aliases: Optional[List[str]] = None) -> None:
        """
        Links this artifact to a portfolio (a promoted collection of artifacts), with aliases.

        Arguments:
            target_path: (str) The path to the portfolio. It must take the form
                {portfolio}, {project}/{portfolio} or {entity}/{project}/{portfolio}.
            aliases: (Optional[List[str]]) A list of strings which uniquely
                identifies the artifact inside the specified portfolio.

        Returns:
            None
        """
        raise NotImplementedError

    def delete(self) -> None:
        """
        Deletes this artifact, cleaning up all files associated with it.

        NOTE: Deletion is permanent and CANNOT be undone.

        Returns:
            None
        """
        raise NotImplementedError

    def wait(self) -> "Artifact":
        """
        Waits for this artifact to finish logging, if needed.

        Returns:
            Artifact
        """
        raise NotImplementedError

    def __getitem__(self, name: str) -> Optional[WBValue]:
        """
        Gets the WBValue object located at the artifact relative `name`.

        NOTE: This will raise an error unless the artifact has been fetched using
        `use_artifact`, fetched using the API, or `wait()` has been called.

        Arguments:
            name: (str) The artifact relative name to get

        Raises:
            Exception: if problem

        Examples:
            Basic usage
            ```
            artifact = wandb.Artifact('my_table', 'dataset')
            table = wandb.Table(columns=["a", "b", "c"], data=[[i, i*2, 2**i]])
            artifact["my_table"] = table

            wandb.log_artifact(artifact)
            ```

            Retrieving an object:
            ```
            artifact = wandb.use_artifact('my_table:latest')
            table = artifact["my_table"]
            ```
        """
        raise NotImplementedError

    def __setitem__(self, name: str, item: WBValue):
        """
        Adds `item` to the artifact at path `name`

        Arguments:
            name: (str) The path within the artifact to add the object.
            item: (wandb.WBValue) The object to add.

        Returns:
            ArtifactManifestEntry: the added manifest entry

        Examples:
            Basic usage
            ```
            artifact = wandb.Artifact('my_table', 'dataset')
            table = wandb.Table(columns=["a", "b", "c"], data=[[i, i*2, 2**i]])
            artifact["my_table"] = table

            wandb.log_artifact(artifact)
            ```

            Retrieving an object:
            ```
            artifact = wandb.use_artifact('my_table:latest')
            table = artifact["my_table"]
            ```
        """
        raise NotImplementedError
